import { test } from "node:test";
import assert from "node:assert/strict";
import { dashboardHtml } from "../src/modules/leads/dashboardHtml.js";

test("daily report shows a search-term column and today's query list", () => {
  const html = dashboardHtml();
  assert.match(html, /<th>คำค้น<\/th>/);
  assert.match(html, /คำค้นวันนี้/);
  assert.match(html, /function searchTermOf/);
  assert.doesNotMatch(html, /attr\.utm_campaign\|\|attr\.keyword/);
});
