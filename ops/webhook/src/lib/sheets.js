import { google } from "googleapis";
import { getConfig } from "../config/env.js";

const LINE_SHEETS = [
  "customers",
  "staff",
  "jobs",
  "checkins",
  "qc_photos",
  "affiliate",
  "payments",
];

const LEAD_SHEETS = [
  "leads",
  "lead_pipeline",
  "lead_attribution",
  "lead_dashboard",
  "ads_conversions",
];

const SHEETS = [...LINE_SHEETS, ...LEAD_SHEETS];

/** leads has 29 columns (beyond Z). Keep all marketing tabs on a wide range. */
export const SHEET_VALUES_RANGE = "A:AZ";

function parseServiceAccount() {
  const raw = getConfig().sheets.serviceAccountJson;
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    // allow base64-encoded JSON
    return JSON.parse(Buffer.from(raw, "base64").toString("utf8"));
  }
}

let _sheets = null;

async function client() {
  if (_sheets) return _sheets;
  const creds = parseServiceAccount();
  if (!creds) {
    throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON missing or invalid");
  }
  const auth = new google.auth.GoogleAuth({
    credentials: creds,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });
  _sheets = google.sheets({ version: "v4", auth });
  return _sheets;
}

function spreadsheetId() {
  return getConfig().sheets.spreadsheetId;
}

/** @returns {Promise<Record<string, string>[]>} */
export async function readTable(sheetName) {
  if (!SHEETS.includes(sheetName)) {
    throw new Error(`Unknown sheet: ${sheetName}`);
  }
  const sheets = await client();
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: spreadsheetId(),
    range: `${sheetName}!${SHEET_VALUES_RANGE}`,
  });
  const rows = res.data.values || [];
  if (rows.length < 2) return [];
  const headers = rows[0].map((h) => String(h).trim());
  return rows.slice(1).map((row) => {
    const obj = {};
    headers.forEach((h, i) => {
      obj[h] = row[i] ?? "";
    });
    return obj;
  });
}

export async function appendRow(sheetName, rowObject) {
  const sheets = await client();
  const existing = await sheets.spreadsheets.values.get({
    spreadsheetId: spreadsheetId(),
    range: `${sheetName}!1:1`,
  });
  const headers = (existing.data.values?.[0] || []).map((h) => String(h).trim());
  if (!headers.length) {
    throw new Error(`Sheet ${sheetName} has no header row`);
  }
  const values = headers.map((h) =>
    rowObject[h] === undefined || rowObject[h] === null
      ? ""
      : String(rowObject[h])
  );
  await sheets.spreadsheets.values.append({
    spreadsheetId: spreadsheetId(),
    range: `${sheetName}!${SHEET_VALUES_RANGE}`,
    valueInputOption: "USER_ENTERED",
    requestBody: { values: [values] },
  });
}

/** Update first row matching predicate; returns true if updated */
export async function updateRow(sheetName, matchFn, patch) {
  const sheets = await client();
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: spreadsheetId(),
    range: `${sheetName}!${SHEET_VALUES_RANGE}`,
  });
  const rows = res.data.values || [];
  if (rows.length < 2) return false;
  const headers = rows[0].map((h) => String(h).trim());
  for (let i = 1; i < rows.length; i++) {
    const obj = {};
    headers.forEach((h, j) => {
      obj[h] = rows[i][j] ?? "";
    });
    if (!matchFn(obj)) continue;
    const next = { ...obj, ...patch };
    const values = headers.map((h) =>
      next[h] === undefined || next[h] === null ? "" : String(next[h])
    );
    const rowNum = i + 1;
    await sheets.spreadsheets.values.update({
      spreadsheetId: spreadsheetId(),
      range: `${sheetName}!A${rowNum}:AZ${rowNum}`,
      valueInputOption: "USER_ENTERED",
      requestBody: { values: [values] },
    });
    return true;
  }
  return false;
}

export async function findCustomerByLineId(lineUserId) {
  const rows = await readTable("customers");
  return rows.find((r) => r.line_user_id === lineUserId) || null;
}

export async function findStaffByLineId(lineUserId) {
  const rows = await readTable("staff");
  return (
    rows.find(
      (r) =>
        r.line_user_id === lineUserId &&
        ["active", "training"].includes(String(r.status).toLowerCase())
    ) || null
  );
}

export function newId(prefix) {
  const t = Date.now().toString(36).toUpperCase();
  const r = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `${prefix}-${t}${r}`;
}
