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

test("attribution.js empty landing is direct", () => {
  const snap = runAttribution("");
  assert.equal(snap.channel, "direct");
  assert.equal(snap.gclid, "");
});
