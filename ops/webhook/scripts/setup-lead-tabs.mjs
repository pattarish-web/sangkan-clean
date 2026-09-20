import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { google } from "googleapis";
import { getConfig } from "../src/config/env.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const headersDir = path.join(__dirname, "../../shared/sheets/headers");
const TABS = [
  "leads",
  "lead_pipeline",
  "lead_attribution",
  "lead_dashboard",
  "ads_conversions",
];

const cfg = getConfig();
const sa = JSON.parse(cfg.sheets.serviceAccountJson);
const spreadsheetId = process.env.LEAD_SHEETS_ID || cfg.sheets.spreadsheetId;
if (!spreadsheetId) throw new Error("GOOGLE_SHEETS_ID or LEAD_SHEETS_ID missing");

const auth = new google.auth.GoogleAuth({
  credentials: sa,
  scopes: ["https://www.googleapis.com/auth/spreadsheets"],
});
const sheets = google.sheets({ version: "v4", auth });

const meta = await sheets.spreadsheets.get({ spreadsheetId });
const existing = new Map(
  (meta.data.sheets || []).map((s) => [s.properties.title, s.properties.sheetId])
);

const requests = [];
for (const title of TABS) {
  if (!existing.has(title)) {
    requests.push({ addSheet: { properties: { title } } });
  }
}
if (requests.length) {
  await sheets.spreadsheets.batchUpdate({
    spreadsheetId,
    requestBody: { requests },
  });
}

for (const tab of TABS) {
  const headerLine = readFileSync(path.join(headersDir, `${tab}.csv`), "utf8")
    .trim()
    .split(/\r?\n/)[0];
  const headers = headerLine.split(",");
  await sheets.spreadsheets.values.update({
    spreadsheetId,
    range: `${tab}!A1`,
    valueInputOption: "RAW",
    requestBody: { values: [headers] },
  });
  console.log("headers_ok", tab, headers.length);
}

console.log("DONE");
console.log("url", `https://docs.google.com/spreadsheets/d/${spreadsheetId}/edit`);
