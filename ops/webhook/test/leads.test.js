import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  validateContactClick,
  validateLeadCreate,
  validateStatusPatch,
  validateContactClickConfirmation,
  normalizePhone,
  adsSafeConversionRow,
  sanitizeAttribution,
} from "../src/lib/leadValidation.js";
import { conversionsToEnqueue, conversionsToCsv } from "../src/lib/adsConversions.js";
import { FileLeadStore } from "../src/lib/leadStore.js";
import { hitRateLimit, resetRateLimits } from "../src/lib/rateLimit.js";

test("normalize Thai mobile numbers", () => {
  assert.equal(normalizePhone("081-234-5678"), "0812345678");
  assert.equal(normalizePhone("+66812345678"), "0812345678");
});

test("reject lead without consent or invalid phone", () => {
  const missing = validateLeadCreate({
    name: "สมชาย",
    phone: "0812345678",
    service: "Big Cleaning",
    consent: false,
  });
  assert.equal(missing.ok, false);
  const badPhone = validateLeadCreate({
    name: "สมชาย",
    phone: "123",
    service: "Big Cleaning",
    consent: true,
  });
  assert.equal(badPhone.error, "phone_invalid");
});

test("honeypot is silently ignored", () => {
  const result = validateLeadCreate({
    name: "bot",
    phone: "0812345678",
    service: "Big Cleaning",
    consent: true,
    honeypot: "http://spam.test",
  });
  assert.equal(result.ok, true);
  assert.equal(result.ignored, true);
});

test("accepts a valid lead and strips unknown attribution keys", () => {
  const result = validateLeadCreate({
    name: "สมชาย ใจดี",
    phone: "0812345678",
    service: "Big Cleaning",
    consent: true,
    attribution: { gclid: "abc", email: "hidden@example.com", name: "nope" },
  });
  assert.equal(result.ok, true);
  assert.equal(result.lead.contact_method, "form");
  assert.equal(result.lead.event_type, "form_submit");
  assert.equal(result.lead.attribution.gclid, "abc");
  assert.equal(result.lead.attribution.email, undefined);
  assert.equal(result.lead.attribution.name, undefined);
});

test("accepts PII-free phone and LINE click records", () => {
  for (const contact_method of ["phone", "line"]) {
    const result = validateContactClick({
      contact_method,
      clicked_target: contact_method === "phone" ? "tel:0929149978" : "https://line.me/ti/p/@sangkanclean",
      page_path: "/landing-bigcleaning.html",
      idempotency_key: `click-${contact_method}-1`,
      attribution: { gclid: "GCLID-CLICK", channel: "google_ads" },
    });
    assert.equal(result.ok, true);
    assert.equal(result.lead.status, "unverified");
    assert.equal(result.lead.event_type, `${contact_method}_click`);
    assert.equal(result.lead.name, "");
    assert.equal(result.lead.phone, "");
    assert.equal(result.lead.attribution.gclid, "GCLID-CLICK");
  }
});

test("rejects unsupported contact click methods", () => {
  const result = validateContactClick({ contact_method: "facebook" });
  assert.equal(result.error, "contact_method_invalid");
});

test("won status requires a value greater than zero", () => {
  const bad = validateStatusPatch({ status: "won", value_thb: 0 });
  assert.equal(bad.error, "won_requires_value");
  const ok = validateStatusPatch({ status: "won", value_thb: 15000 });
  assert.equal(ok.ok, true);
});

test("Ads conversion rows never include PII", () => {
  const row = adsSafeConversionRow(
    {
      id: "LD-1",
      name: "SECRET",
      phone: "0812345678",
      message: "บ้านฉัน",
      gclid: "GCLID-1",
      value_thb: 9900,
    },
    "won_deal",
    "2026-09-19 10:00:00+07:00"
  );
  const blob = JSON.stringify(row);
  assert.equal(row.gclid, "GCLID-1");
  assert.equal(row.conversion_currency, "THB");
  assert.doesNotMatch(blob, /SECRET|0812345678|บ้านฉัน/);
});

test("qualified and won conversions enqueue once when GCLID exists", () => {
  const lead = {
    id: "LD-2",
    status: "won",
    gclid: "GCLID-2",
    value_thb: 12000,
    ads_qualified_sent_at: "",
    ads_won_sent_at: "",
  };
  const rows = conversionsToEnqueue(lead, "new");
  assert.equal(rows.length, 2);
  assert.deepEqual(
    rows.map((r) => r.conversion_name),
    ["qualified_lead", "won_deal"]
  );
  const csv = conversionsToCsv(rows);
  assert.match(csv, /Google Click ID/);
  assert.doesNotMatch(csv, /SECRET|0812345678|@/);
});

test("no Ads conversion without GCLID", () => {
  const rows = conversionsToEnqueue(
    { id: "LD-3", status: "won", value_thb: 1000, attribution: {} },
    "new"
  );
  assert.equal(rows.length, 0);
});

test("rate limiter blocks after limit", () => {
  resetRateLimits();
  assert.equal(hitRateLimit("t", { limit: 2, windowMs: 60_000 }).ok, true);
  assert.equal(hitRateLimit("t", { limit: 2, windowMs: 60_000 }).ok, true);
  assert.equal(hitRateLimit("t", { limit: 2, windowMs: 60_000 }).ok, false);
});

test("file store is idempotent and queues Ads conversions", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "leads-"));
  const store = new FileLeadStore(path.join(dir, "leads.json"));
  const payload = {
    name: "ทดสอบ",
    phone: "0812345678",
    service: "Big Cleaning",
    area: "บางนา",
    message: "งานบ้าน",
    consent: true,
    page_path: "/",
    idempotency_key: "abc-1",
    attribution: { gclid: "GCLID-STORE", channel: "google_ads" },
  };
  const first = await store.create(payload, { ip: "127.0.0.1" });
  const second = await store.create(payload, { ip: "127.0.0.1" });
  assert.equal(first.duplicate, false);
  assert.equal(second.duplicate, true);
  assert.equal(first.lead.id, second.lead.id);
  assert.equal(first.lead.contact_method, "form");
  assert.equal(first.lead.event_type, "form_submit");
  const updated = await store.updateStatus(first.lead.id, {
    status: "won",
    value_thb: 8500,
    lost_reason: "",
    note: "",
  });
  assert.equal(updated.queued.length, 2);
  const csvSafe = JSON.stringify(updated.queued);
  assert.doesNotMatch(csvSafe, /ทดสอบ|0812345678|งานบ้าน/);
  await rm(dir, { recursive: true, force: true });
});

test("staff can identify an unverified click after checking phone history", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "clicks-"));
  const store = new FileLeadStore(path.join(dir, "leads.json"));
  const created = await store.create({
    name: "",
    phone: "",
    service: "คลิกโทรจากเว็บไซต์",
    status: "unverified",
    contact_method: "phone",
    event_type: "phone_click",
    consent: false,
    page_path: "/",
    idempotency_key: "phone-click-1",
    attribution: { gclid: "GCLID-PHONE", channel: "google_ads" },
  });
  const updated = await store.updateStatus(created.lead.id, {
    status: "contacted",
    value_thb: null,
    lost_reason: "",
    note: "",
    name: "ลูกค้าจากสายโทร",
    phone: "0812345678",
    service: "Big Cleaning",
    area: "บางนา",
  });
  assert.equal(updated.lead.status, "contacted");
  assert.equal(updated.lead.name, "ลูกค้าจากสายโทร");
  assert.equal(updated.lead.phone, "0812345678");
  assert.equal(updated.queued.length, 1);
  assert.equal(updated.queued[0].conversion_name, "phone_click");
  assert.equal(updated.queued[0].gclid, "GCLID-PHONE");
  assert.equal(updated.lead.ads_contact_sent_at !== "", true);
  const csvSafe = JSON.stringify(updated.queued);
  assert.doesNotMatch(csvSafe, /ลูกค้าจากสายโทร|0812345678/);
  const summary = await store.summary(updated.lead.created_date_bkk);
  assert.equal(summary.byContactMethod.phone, 1);
  assert.equal(summary.adsUpload.pending, 1);
  assert.equal(summary.adsUpload.uploaded, 0);
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
  const after = await store.summary(updated.lead.created_date_bkk);
  assert.equal(after.adsUpload.pending, 0);
  assert.equal(after.adsUpload.uploaded, 1);
  assert.equal((await store.pendingConversions()).length, 0);
  await rm(dir, { recursive: true, force: true });
});

test("LINE click queues Ads only after staff confirmation", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "line-clicks-"));
  const store = new FileLeadStore(path.join(dir, "leads.json"));
  const created = await store.create({
    name: "",
    phone: "",
    service: "คลิก LINE จากเว็บไซต์",
    status: "unverified",
    contact_method: "line",
    event_type: "line_click",
    consent: false,
    page_path: "/",
    idempotency_key: "line-click-1",
    attribution: { gclid: "GCLID-LINE", channel: "google_ads" },
  });
  const lost = await store.updateStatus(created.lead.id, {
    status: "lost",
    lost_reason: "กดผิด",
    note: "",
  });
  assert.equal(lost.queued.length, 0);
  const confirmed = await store.updateStatus(created.lead.id, {
    status: "contacted",
    name: "ลูกค้าจากไลน์",
    phone: "0891112233",
    lost_reason: "",
    note: "",
  });
  assert.equal(confirmed.queued.length, 1);
  assert.equal(confirmed.queued[0].conversion_name, "line_click");
  await rm(dir, { recursive: true, force: true });
});

test("confirming a phone click requires name and phone", () => {
  const existing = {
    status: "unverified",
    contact_method: "phone",
    event_type: "phone_click",
    name: "",
    phone: "",
  };
  const missingName = validateContactClickConfirmation(existing, {
    status: "contacted",
    name: "",
    phone: "0812345678",
  });
  assert.equal(missingName.error, "confirm_name_required");
  const missingPhone = validateContactClickConfirmation(existing, {
    status: "contacted",
    name: "สมชาย",
    phone: "",
  });
  assert.equal(missingPhone.error, "confirm_phone_required");
  const ok = validateContactClickConfirmation(existing, {
    status: "contacted",
    name: "สมชาย",
    phone: "0812345678",
  });
  assert.equal(ok.ok, true);
  const lostOk = validateContactClickConfirmation(existing, {
    status: "lost",
    lost_reason: "สแปม",
  });
  assert.equal(lostOk.ok, true);
});

test("unverified phone click does not enqueue Ads until confirmed", () => {
  const rows = conversionsToEnqueue(
    {
      id: "LD-CLICK",
      status: "unverified",
      contact_method: "phone",
      event_type: "phone_click",
      gclid: "GCLID-WAIT",
      ads_contact_sent_at: "",
    },
    "unverified"
  );
  assert.equal(rows.length, 0);
});

test("confirming a phone click as qualified queues phone_click then qualified_lead", () => {
  const rows = conversionsToEnqueue(
    {
      id: "LD-Q",
      status: "qualified",
      contact_method: "phone",
      event_type: "phone_click",
      gclid: "GCLID-Q",
      created_at: "2026-09-19T03:00:00.000Z",
      ads_contact_sent_at: "",
      ads_qualified_sent_at: "",
    },
    "unverified"
  );
  assert.deepEqual(
    rows.map((r) => r.conversion_name),
    ["phone_click", "qualified_lead"]
  );
  assert.equal(rows[0].conversion_time, "2026-09-19T03:00:00+00:00");
});

test("form leads never enqueue phone_click or line_click", () => {
  const rows = conversionsToEnqueue(
    {
      id: "LD-FORM",
      status: "won",
      contact_method: "form",
      event_type: "form_submit",
      gclid: "GCLID-FORM",
      value_thb: 5000,
      ads_qualified_sent_at: "",
      ads_won_sent_at: "",
    },
    "new"
  );
  assert.deepEqual(
    rows.map((r) => r.conversion_name),
    ["qualified_lead", "won_deal"]
  );
});

test("website does not fire Google Ads conversions on raw phone or LINE clicks", async () => {
  const tracking = await readFile(new URL("../../../tracking.js", import.meta.url), "utf8");
  const leadForm = await readFile(new URL("../../../lead-form.js", import.meta.url), "utf8");
  assert.match(tracking, /captureContactClick\('phone'/);
  assert.match(tracking, /captureContactClick\('line'/);
  assert.doesNotMatch(tracking, /fireAdsConversion\(\s*'phone'/);
  assert.doesNotMatch(tracking, /fireAdsConversion\(\s*'line'/);
  assert.match(tracking, /fireAdsConversion\('lead'/);
  assert.match(tracking, /generate_lead/);
  assert.match(tracking, /sangkan-office-ops\.onrender\.com\/api\/leads/);
  assert.match(tracking, /preserveClickIdsOnQuoteLinks/);
  assert.match(leadForm, /sangkan-office-ops\.onrender\.com\/api\/leads/);
  assert.doesNotMatch(leadForm, /generate_lead/);
  assert.doesNotMatch(leadForm, /fireAdsConversion/);
});

test("Ads landings have an on-page quote form that posts to the Lead API scripts", async () => {
  const big = await readFile(new URL("../../../landing-bigcleaning.html", import.meta.url), "utf8");
  const maid = await readFile(new URL("../../../landing-maid.html", import.meta.url), "utf8");
  assert.match(big, /id="quoteForm"/);
  assert.match(maid, /id="quoteForm"/);
  assert.match(big, /name="consent"/);
  assert.match(maid, /name="consent"/);
  assert.match(big, /lead-form\.js/);
  assert.match(maid, /lead-form\.js/);
});

test("sanitizeAttribution drops PII-like keys", () => {
  const out = sanitizeAttribution({
    gclid: "x",
    phone: "0812345678",
    message: "hi",
  });
  assert.equal(out.gclid, "x");
  assert.equal(out.phone, undefined);
});
