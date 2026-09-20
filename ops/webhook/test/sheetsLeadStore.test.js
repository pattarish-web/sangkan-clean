import { test } from "node:test";
import assert from "node:assert/strict";
import { SheetsLeadStore } from "../src/lib/sheetsLeadStore.js";
import {
  LEAD_HEADERS,
  memoryLeadIo,
  pickSharedLeadSpreadsheet,
  planLeadTabSetup,
} from "../src/lib/leadSheetMap.js";
import { normalizeSpreadsheetId, SHEET_VALUES_RANGE } from "../src/lib/sheets.js";

test("Sheets value range covers all lead columns", () => {
  assert.equal(LEAD_HEADERS.length, 29);
  assert.equal(SHEET_VALUES_RANGE, "A:AZ");
});

test("planLeadTabSetup renames Sheet1 and adds the other lead tabs", () => {
  const plan = planLeadTabSetup(["Sheet1"]);
  assert.deepEqual(plan.rename, [{ from: "Sheet1", to: "leads" }]);
  assert.deepEqual(plan.add, [
    "lead_pipeline",
    "lead_attribution",
    "lead_dashboard",
    "ads_conversions",
  ]);
});

test("planLeadTabSetup renames a google ads tab to leads", () => {
  const plan = planLeadTabSetup(["google ads"]);
  assert.deepEqual(plan.rename, [{ from: "google ads", to: "leads" }]);
  assert.equal(plan.add.includes("leads"), false);
});

test("normalizeSpreadsheetId accepts a full Sheets URL", () => {
  const id = "1AbCdefGhijkLMNOPQRstuVWXYZ0123456789-_";
  assert.equal(
    normalizeSpreadsheetId(`https://docs.google.com/spreadsheets/d/${id}/edit?gid=0#gid=0`),
    id
  );
  assert.equal(normalizeSpreadsheetId(id), id);
});

test("pickSharedLeadSpreadsheet prefers the google ads file", () => {
  const picked = pickSharedLeadSpreadsheet([
    { id: "other", name: "Office Ops" },
    { id: "leads-file", name: "google ads" },
  ]);
  assert.equal(picked.id, "leads-file");
  assert.equal(pickSharedLeadSpreadsheet([{ id: "only", name: "My Sheet" }]).id, "only");
  assert.equal(pickSharedLeadSpreadsheet([]), null);
});

test("Sheets lead store is idempotent and queues Ads conversions without PII", async () => {
  const io = memoryLeadIo();
  const store = new SheetsLeadStore(io);
  const payload = {
    name: "ทดสอบ",
    phone: "0812345678",
    service: "Big Cleaning",
    area: "บางนา",
    message: "งานบ้าน",
    consent: true,
    page_path: "/",
    idempotency_key: "sheet-form-1",
    attribution: { gclid: "GCLID-SHEET", channel: "google_ads" },
  };
  const first = await store.create(payload);
  const second = await store.create(payload);
  assert.equal(first.duplicate, false);
  assert.equal(second.duplicate, true);
  assert.equal(first.lead.contact_method, "form");
  assert.equal(first.lead.event_type, "form_submit");
  const updated = await store.updateStatus(first.lead.id, {
    status: "won",
    value_thb: 8500,
    lost_reason: "",
    note: "",
  });
  assert.equal(updated.queued.length, 2);
  assert.deepEqual(
    updated.queued.map((row) => row.conversion_name),
    ["qualified_lead", "won_deal"]
  );
  const blob = JSON.stringify(updated.queued);
  assert.doesNotMatch(blob, /ทดสอบ|0812345678|งานบ้าน/);
  const pending = await store.pendingConversions();
  assert.equal(pending.length, 2);
  await store.markConversionUploads([
    {
      order_id: pending[0].order_id,
      conversion_name: pending[0].conversion_name,
      upload_status: "uploaded",
      uploaded_at: "2026-09-19T12:00:00.000Z",
      upload_error: "",
    },
  ]);
  const after = await store.pendingConversions();
  assert.equal(after.length, 1);
  const summary = await store.summary(first.lead.created_date_bkk);
  assert.equal(summary.byContactMethod.form, 1);
  assert.equal(summary.adsUpload.uploaded, 1);
  assert.equal(summary.adsUpload.pending, 1);
});

test("Sheets store confirms a phone click then marks the Ads upload", async () => {
  const store = new SheetsLeadStore(memoryLeadIo());
  const created = await store.create({
    name: "",
    phone: "",
    service: "คลิกโทรจากเว็บไซต์",
    status: "unverified",
    contact_method: "phone",
    event_type: "phone_click",
    consent: false,
    page_path: "/",
    idempotency_key: "sheet-phone-1",
    attribution: { gclid: "GCLID-SHEET-PHONE", channel: "google_ads" },
  });
  assert.equal(created.lead.contact_method, "phone");
  assert.equal(created.lead.status, "unverified");
  const lost = await store.updateStatus(created.lead.id, {
    status: "lost",
    lost_reason: "กดผิด",
    note: "",
  });
  assert.equal(lost.queued.length, 0);
  const confirmed = await store.updateStatus(created.lead.id, {
    status: "contacted",
    name: "ลูกค้าจากสายโทร",
    phone: "0812345678",
    lost_reason: "",
    note: "",
  });
  assert.equal(confirmed.queued.length, 1);
  assert.equal(confirmed.queued[0].conversion_name, "phone_click");
  assert.doesNotMatch(JSON.stringify(confirmed.queued), /ลูกค้าจากสายโทร|0812345678/);
  const pending = await store.pendingConversions();
  assert.equal(pending.length, 1);
  await store.markConversionUploads([
    {
      order_id: pending[0].order_id,
      conversion_name: "phone_click",
      upload_status: "uploaded",
      uploaded_at: "2026-09-19T12:00:00.000Z",
      upload_error: "",
    },
  ]);
  assert.equal((await store.pendingConversions()).length, 0);
});
