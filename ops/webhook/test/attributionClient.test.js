import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");

function runAttribution(search, cookies = "") {
  const code = readFileSync(path.join(root, "attribution.js"), "utf8");
  const store = {};
  const sandbox = {
    window: {},
    location: { search, pathname: "/landing-bigcleaning.html", hash: "" },
    document: { cookie: cookies, referrer: "" },
    Date,
    URL,
    URLSearchParams,
    localStorage: {
      getItem: (k) => store[k] || null,
      setItem: (k, v) => {
        store[k] = String(v);
      },
    },
  };
  sandbox.window = sandbox;
  vm.runInNewContext(code, sandbox);
  return sandbox.window.SangkanAttribution.snapshot();
}

test("attribution.js marks gclid landing as google_ads", () => {
  const snap = runAttribution("?gclid=TESTGCLID123&utm_source=google&utm_medium=cpc");
  assert.equal(snap.channel, "google_ads");
  assert.equal(snap.gclid, "TESTGCLID123");
});

test("attribution.js reads Google _gcl_aw cookie when URL has no gclid", () => {
  const snap = runAttribution("", "_gcl_aw=GCL.1710000000.CjwCookieGclid");
  assert.equal(snap.gclid, "CjwCookieGclid");
  assert.equal(snap.channel, "google_ads");
});

test("attribution.js captures searchterm from the landing URL", () => {
  const snap = runAttribution(
    "?gclid=TESTGCLID123&keyword=%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%97%E0%B8%B3%E0%B8%84%E0%B8%A7%E0%B8%B2%E0%B8%A1%E0%B8%AA%E0%B8%B0%E0%B8%AD%E0%B8%B2%E0%B8%94%E0%B8%9A%E0%B9%89%E0%B8%B2%E0%B8%99&searchterm=%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%97%E0%B8%B3%E0%B8%84%E0%B8%A7%E0%B8%B2%E0%B8%A1%E0%B8%AA%E0%B8%B0%E0%B8%AD%E0%B8%B2%E0%B8%94%E0%B8%9A%E0%B9%89%E0%B8%B2%E0%B8%99%E0%B9%83%E0%B8%81%E0%B8%A5%E0%B9%89%E0%B8%89%E0%B8%B1%E0%B8%99"
  );
  assert.equal(snap.channel, "google_ads");
  assert.equal(snap.keyword, "รับทำความสะอาดบ้าน");
  assert.equal(snap.searchterm, "รับทำความสะอาดบ้านใกล้ฉัน");
});

test("attribution.js drops unreplaced ValueTrack tokens", () => {
  const snap = runAttribution("?gclid=TESTGCLID123&keyword={keyword}&searchterm={searchterm}");
  assert.equal(snap.gclid, "TESTGCLID123");
  assert.equal(snap.keyword, "");
  assert.equal(snap.searchterm, "");
});

test("attribution.js copies keyword into searchterm when searchterm is missing", () => {
  const snap = runAttribution(
    "?gclid=TESTGCLID123&keyword=%E0%B8%A3%E0%B8%B1%E0%B8%9A%E0%B8%97%E0%B8%B3%E0%B8%84%E0%B8%A7%E0%B8%B2%E0%B8%A1%E0%B8%AA%E0%B8%B0%E0%B8%AD%E0%B8%B2%E0%B8%94%E0%B8%9A%E0%B9%89%E0%B8%B2%E0%B8%99"
  );
  assert.equal(snap.keyword, "รับทำความสะอาดบ้าน");
  assert.equal(snap.searchterm, "รับทำความสะอาดบ้าน");
});
