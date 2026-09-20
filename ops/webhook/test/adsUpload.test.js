import { afterEach, describe, test } from "node:test";
import assert from "node:assert/strict";
import { Readable } from "node:stream";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import {
  adsConfigured,
  adsDateTime,
  clickConversionBody,
  payloadHasPii,
  setAdsConfigOverride,
  setAdsFetch,
  uploadClickConversions,
} from "../src/lib/adsUpload.js";
import { FileLeadStore, setLeadStore } from "../src/lib/leadStore.js";
import { dashboardHtml } from "../src/modules/leads/dashboardHtml.js";
import { handleLeadRequest } from "../src/modules/leads/index.js";

describe("ads upload", { concurrency: false }, () => {
afterEach(() => {
  setAdsConfigOverride(null);
  setAdsFetch(null);
});

function jsonRes(obj, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(obj),
  };
}

test("adsDateTime converts ISO to Ads space format", () => {
  assert.equal(adsDateTime("2026-09-19T18:30:32+00:00"), "2026-09-19 18:30:32+00:00");
  assert.equal(adsDateTime("2026-09-19T18:30:32.000Z"), "2026-09-19 18:30:32+00:00");
});

test("click conversion body is GCLID-only", () => {
  const body = clickConversionBody(
    {
      gclid: "GCLID-1",
      conversion_name: "phone_click",
      conversion_time: "2026-09-19T18:30:32.000Z",
      conversion_currency: "THB",
      order_id: "LD-1",
      conversion_value: "",
      name: "SECRET",
      phone: "0812345678",
    },
    "customers/6151208199/conversionActions/1"
  );
  const blob = JSON.stringify(body);
  assert.equal(body.gclid, "GCLID-1");
  assert.equal(body.orderId, "LD-1");
  assert.equal(body.currencyCode, "THB");
  assert.doesNotMatch(blob, /SECRET|0812345678|"name"|"phone"/);
  assert.equal(payloadHasPii(body), false);
});

test("uploadClickConversions skips when Ads is not configured", async () => {
  setAdsConfigOverride({
    developerToken: "",
    clientId: "",
    clientSecret: "",
    refreshToken: "",
    customerId: "6151208199",
    loginCustomerId: "7915729299",
    apiVersion: "v19",
  });
  assert.equal(adsConfigured(), false);
  const result = await uploadClickConversions([
    {
      gclid: "GCLID-1",
      conversion_name: "phone_click",
      conversion_time: "2026-09-19T18:30:32.000Z",
      order_id: "LD-1",
      upload_status: "pending",
    },
  ]);
  assert.equal(result.skipped, true);
  assert.equal(result.reason, "not_configured");
  assert.equal(result.results[0].upload_status, "pending");
});

test("adsConfigured is true with Cloud OAuth only", () => {
  setAdsConfigOverride({
    developerToken: "",
    clientId: "id",
    clientSecret: "secret",
    refreshToken: "refresh",
    customerId: "6151208199",
    loginCustomerId: "7915729299",
    apiVersion: "v19",
  });
  assert.equal(adsConfigured(), true);
});

test("uploadClickConversions posts mocked click conversions without PII", async () => {
  const calls = [];
  setAdsConfigOverride({
    developerToken: "",
    clientId: "id",
    clientSecret: "secret",
    refreshToken: "refresh",
    customerId: "6151208199",
    loginCustomerId: "7915729299",
    apiVersion: "v19",
  });
  setAdsFetch(async (url, opts) => {
    calls.push({
      url: String(url),
      body: String(opts.body || ""),
      headers: opts.headers || {},
    });
    if (String(url).includes("oauth2")) {
      return jsonRes({ access_token: "tok", expires_in: 3600 });
    }
    if (String(url).includes("googleAds:search")) {
      return jsonRes({
        results: [
          {
            conversionAction: {
              name: "phone_click",
              resourceName: "customers/6151208199/conversionActions/1",
            },
          },
        ],
      });
    }
    if (String(url).includes("uploadClickConversions")) {
      return jsonRes({ results: [{ gclid: "GCLID-1" }] });
    }
    throw new Error("unexpected " + url);
  });
  const result = await uploadClickConversions([
    {
      gclid: "GCLID-1",
      conversion_name: "phone_click",
      conversion_time: "2026-09-19T18:30:32.000Z",
      conversion_currency: "THB",
      order_id: "LD-1",
      upload_status: "pending",
      name: "SECRET",
      phone: "0812345678",
    },
  ]);
  assert.equal(result.skipped, false);
  assert.equal(result.uploaded, 1);
  assert.equal(result.failed, 0);
  const uploadCall = calls.find((c) => c.url.includes("uploadClickConversions"));
  assert.ok(uploadCall);
  assert.doesNotMatch(uploadCall.body, /SECRET|0812345678|"name"|"phone"|"email"|"message"/);
  assert.match(uploadCall.body, /"gclid":"GCLID-1"/);
  assert.match(uploadCall.body, /"orderId":"LD-1"/);
  assert.equal(payloadHasPii(JSON.parse(uploadCall.body)), false);
  assert.equal(uploadCall.headers["developer-token"], undefined);
});

test("dashboard includes Ads API retry control", () => {
  const html = dashboardHtml();
  assert.match(html, /ads-conversions\/upload/);
  assert.match(html, /ส่งคิวเข้า Google Ads/);
  assert.match(html, /adsUpload/);
  assert.match(html, /Authorization: "Bearer "/);
  assert.doesNotMatch(html, /ads-conversions\.csv\?token=/);
  assert.match(html, /byContactMethod\.form/);
  assert.match(html, /ชื่อลูกค้า/);
  assert.match(html, /lead-name-input/);
  assert.match(html, /isConfirm && status === "unverified"/);
});

function makeReq({ method, url, body, token }) {
  const raw = body ? Buffer.from(JSON.stringify(body)) : Buffer.alloc(0);
  const req = Readable.from([raw]);
  req.method = method;
  req.url = url;
  req.headers = {
    authorization: token ? "Bearer " + token : "",
    "content-type": "application/json",
    origin: "http://127.0.0.1",
  };
  return req;
}

function makeRes() {
  return {
    statusCode: 0,
    headers: {},
    body: "",
    writeHead(code, headers) {
      this.statusCode = code;
      this.headers = headers || {};
    },
    end(chunk) {
      this.body = chunk || "";
    },
  };
}

test("confirming a click uploads immediately when Ads is mocked", async () => {
  process.env.LEAD_STAFF_TOKEN = "test-staff";
  const dir = await mkdtemp(path.join(os.tmpdir(), "ads-http-"));
  const store = new FileLeadStore(path.join(dir, "leads.json"));
  setLeadStore(store);
  const created = await store.create({
    name: "",
    phone: "",
    service: "คลิกโทรจากเว็บไซต์",
    status: "unverified",
    contact_method: "phone",
    event_type: "phone_click",
    consent: false,
    page_path: "/",
    idempotency_key: "phone-click-http-1",
    attribution: { gclid: "GCLID-HTTP", channel: "google_ads" },
  });
  setAdsConfigOverride({
    developerToken: "dev",
    clientId: "id",
    clientSecret: "secret",
    refreshToken: "refresh",
    customerId: "6151208199",
    loginCustomerId: "7915729299",
    apiVersion: "v19",
  });
  const uploadBodies = [];
  setAdsFetch(async (url, opts) => {
    if (String(url).includes("oauth2")) return jsonRes({ access_token: "tok", expires_in: 3600 });
    if (String(url).includes("googleAds:search")) {
      return jsonRes({
        results: [
          {
            conversionAction: {
              name: "phone_click",
              resourceName: "customers/6151208199/conversionActions/1",
            },
          },
        ],
      });
    }
    if (String(url).includes("uploadClickConversions")) {
      uploadBodies.push(String(opts.body || ""));
      return jsonRes({ results: [{ gclid: "GCLID-HTTP" }] });
    }
    throw new Error("unexpected " + url);
  });
  const req = makeReq({
    method: "PATCH",
    url: "/api/leads/" + created.lead.id,
    token: "test-staff",
    body: {
      status: "contacted",
      name: "ลูกค้าจากสายโทร",
      phone: "0812345678",
    },
  });
  const res = makeRes();
  const handled = await handleLeadRequest(req, res, new URL(req.url, "http://local"));
  assert.equal(handled, true);
  assert.equal(res.statusCode, 200);
  const payload = JSON.parse(res.body);
  assert.equal(payload.ok, true);
  assert.equal(payload.queued_conversions, 1);
  assert.equal(payload.ads_upload.uploaded, 1);
  assert.equal(payload.ads_upload.skipped, false);
  assert.equal(uploadBodies.length, 1);
  assert.doesNotMatch(uploadBodies[0], /ลูกค้าจากสายโทร|0812345678/);
  const pending = await store.pendingConversions();
  assert.equal(pending.length, 0);
  setLeadStore(null);
  await rm(dir, { recursive: true, force: true });
});

test("confirm still succeeds when Ads is unconfigured", async () => {
  process.env.LEAD_STAFF_TOKEN = "test-staff";
  const dir = await mkdtemp(path.join(os.tmpdir(), "ads-skip-"));
  const store = new FileLeadStore(path.join(dir, "leads.json"));
  setLeadStore(store);
  const created = await store.create({
    name: "",
    phone: "",
    service: "คลิก LINE จากเว็บไซต์",
    status: "unverified",
    contact_method: "line",
    event_type: "line_click",
    consent: false,
    page_path: "/",
    idempotency_key: "line-click-http-1",
    attribution: { gclid: "GCLID-SKIP", channel: "google_ads" },
  });
  setAdsConfigOverride({
    developerToken: "",
    clientId: "",
    clientSecret: "",
    refreshToken: "",
    customerId: "6151208199",
    loginCustomerId: "7915729299",
    apiVersion: "v19",
  });
  const req = makeReq({
    method: "PATCH",
    url: "/api/leads/" + created.lead.id,
    token: "test-staff",
    body: {
      status: "contacted",
      name: "ลูกค้าจากไลน์",
      phone: "0891112233",
    },
  });
  const res = makeRes();
  await handleLeadRequest(req, res, new URL(req.url, "http://local"));
  assert.equal(res.statusCode, 200);
  const payload = JSON.parse(res.body);
  assert.equal(payload.ok, true);
  assert.equal(payload.ads_upload.skipped, true);
  assert.equal(payload.ads_upload.reason, "not_configured");
  assert.equal((await store.pendingConversions()).length, 1);
  setLeadStore(null);
  await rm(dir, { recursive: true, force: true });
});

test("CSV export is pending-only, staff-authorized, and PII-free", async () => {
  process.env.LEAD_STAFF_TOKEN = "test-staff";
  const dir = await mkdtemp(path.join(os.tmpdir(), "ads-csv-"));
  const store = new FileLeadStore(path.join(dir, "leads.json"));
  setLeadStore(store);
  const created = await store.create({
    name: "ลูกค้าฟอร์ม",
    phone: "0812345678",
    service: "Big Cleaning",
    status: "new",
    contact_method: "form",
    event_type: "form_submit",
    consent: true,
    page_path: "/",
    idempotency_key: "form-csv-1",
    attribution: { gclid: "GCLID-CSV", channel: "google_ads" },
  });
  await store.updateStatus(created.lead.id, {
    status: "qualified",
    value_thb: null,
    lost_reason: "",
    note: "",
  });
  await store.markConversionUploads([
    {
      order_id: created.lead.id,
      conversion_name: "qualified_lead",
      upload_status: "uploaded",
      uploaded_at: "2026-09-19T12:00:00.000Z",
      upload_error: "",
    },
  ]);
  await store.updateStatus(created.lead.id, {
    status: "won",
    value_thb: 12000,
    lost_reason: "",
    note: "",
  });
  const denied = makeRes();
  await handleLeadRequest(
    makeReq({ method: "GET", url: "/api/leads/ads-conversions.csv" }),
    denied,
    new URL("/api/leads/ads-conversions.csv", "http://local")
  );
  assert.equal(denied.statusCode, 401);
  const allowed = makeRes();
  const req = makeReq({
    method: "GET",
    url: "/api/leads/ads-conversions.csv",
    token: "test-staff",
  });
  await handleLeadRequest(req, allowed, new URL(req.url, "http://local"));
  assert.equal(allowed.statusCode, 200);
  assert.match(allowed.body, /won_deal/);
  assert.doesNotMatch(allowed.body, /qualified_lead/);
  assert.doesNotMatch(allowed.body, /ลูกค้าฟอร์ม|0812345678/);
  setLeadStore(null);
  await rm(dir, { recursive: true, force: true });
});
});
