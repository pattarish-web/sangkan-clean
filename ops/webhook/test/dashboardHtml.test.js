import { test } from "node:test";
import assert from "node:assert/strict";
import { dashboardHtml } from "../src/modules/leads/dashboardHtml.js";

test("daily report shows a search-term column and today's query list", () => {
  const html = dashboardHtml();
  assert.match(html, /<th>คำค้น<\/th>/);
  assert.match(html, /คีย์เวิร์ดจากลีดวันนี้/);
  assert.match(html, /คำค้นจริงจาก Ads วันนี้/);
  assert.match(html, /function searchTermOf/);
  assert.match(html, /function renderAdsSearchTerms/);
  assert.match(html, /attr\.searchterm \|\| attr\.utm_term \|\| attr\.keyword/);
  assert.doesNotMatch(html, /attr\.utm_campaign\|\|attr\.keyword/);
});
