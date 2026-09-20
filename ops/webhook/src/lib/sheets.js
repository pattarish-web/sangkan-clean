import { google } from "googleapis";
import { getConfig } from "../config/env.js";
import {
  LEAD_TAB_HEADERS,
  LEAD_TABS,
  pickSharedLeadSpreadsheet,
  planLeadTabSetup,
} from "./leadSheetMap.js";

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
  let creds;
  try {
    creds = JSON.parse(raw);
  } catch {
    try {
      creds = JSON.parse(Buffer.from(raw, "base64").toString("utf8"));
    } catch {
      return null;
    }
  }
  if (!creds || typeof creds !== "object") return null;
  if (creds.web || creds.installed) return null;
  if (!creds.private_key || !creds.client_email) return null;
  return creds;
}

/** Accept a raw ID or a full Google Sheets URL. */
export function normalizeSpreadsheetId(raw) {
  const value = String(raw || "").trim();
  const fromUrl = value.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
  return fromUrl ? fromUrl[1] : value;
}

function sheetsErrorMessage(err) {
  const g = err?.response?.data?.error;
  if (g?.message) return String(g.message);
  return String(err?.message || "sheets_error");
}

let _auth = null;
let _sheets = null;
let _resolvedSpreadsheetId = "";
let _resolvedSpreadsheetSource = "";

async function getAuth() {
  if (_auth) return _auth;
  const creds = parseServiceAccount();
  if (!creds) {
    throw new Error("GOOGLE_SERVICE_ACCOUNT_JSON missing or invalid");
  }
  _auth = new google.auth.GoogleAuth({
    credentials: creds,
    scopes: [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive.metadata.readonly",
    ],
  });
  return _auth;
}

async function client() {
  if (_sheets) return _sheets;
  _sheets = google.sheets({ version: "v4", auth: await getAuth() });
  return _sheets;
}

function configuredSpreadsheetId() {
  return normalizeSpreadsheetId(getConfig().sheets.spreadsheetId);
}

function isNotFoundError(err) {
  const status = err?.response?.status || err?.code;
  if (status === 404) return true;
  return /not found/i.test(sheetsErrorMessage(err));
}

async function listSharedSpreadsheets() {
  const drive = google.drive({ version: "v3", auth: await getAuth() });
  const queries = [
    "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
    "sharedWithMe and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
  ];
  const found = new Map();
  for (const q of queries) {
    try {
      const listed = await drive.files.list({
        q,
        fields: "files(id,name)",
        pageSize: 50,
        supportsAllDrives: true,
        includeItemsFromAllDrives: true,
      });
      for (const file of listed.data.files || []) {
        if (file?.id) found.set(file.id, file);
      }
    } catch (err) {
      if (queries.indexOf(q) === queries.length - 1 && found.size === 0) throw err;
    }
  }
  return [...found.values()];
}

async function resolveSpreadsheetId() {
  if (_resolvedSpreadsheetId) return _resolvedSpreadsheetId;
  const sheets = await client();
  const configured = configuredSpreadsheetId();
  if (configured) {
    try {
      await sheets.spreadsheets.get({
        spreadsheetId: configured,
        fields: "spreadsheetId",
      });
      _resolvedSpreadsheetId = configured;
      _resolvedSpreadsheetSource = "configured";
      return _resolvedSpreadsheetId;
    } catch (err) {
      if (!isNotFoundError(err)) throw err;
    }
  }
  const picked = pickSharedLeadSpreadsheet(await listSharedSpreadsheets());
  if (!picked?.id) {
    throw new Error(
      "Requested entity was not found. Share the google ads spreadsheet with the service account, or set GOOGLE_SHEETS_ID to that file's ID."
    );
  }
  _resolvedSpreadsheetId = picked.id;
  _resolvedSpreadsheetSource = "shared_file";
  return _resolvedSpreadsheetId;
}

/** @returns {Promise<Record<string, string>[]>} */
export async function readTable(sheetName) {
  if (!SHEETS.includes(sheetName)) {
    throw new Error(`Unknown sheet: ${sheetName}`);
  }
  const sheets = await client();
  const id = await resolveSpreadsheetId();
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: id,
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
  const id = await resolveSpreadsheetId();
  const existing = await sheets.spreadsheets.values.get({
    spreadsheetId: id,
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
    spreadsheetId: id,
    range: `${sheetName}!${SHEET_VALUES_RANGE}`,
    valueInputOption: "USER_ENTERED",
    requestBody: { values: [values] },
  });
}

/** Update first row matching predicate; returns true if updated */
export async function updateRow(sheetName, matchFn, patch) {
  const sheets = await client();
  const id = await resolveSpreadsheetId();
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: id,
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
      spreadsheetId: id,
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

/** Create marketing lead tabs + header rows. Safe to run repeatedly. */
export async function ensureLeadTabs() {
  const creds = parseServiceAccount();
  if (!creds) {
    return { ok: false, skipped: true, reason: "sheets_unconfigured" };
  }
  try {
    const sheets = await client();
    const id = await resolveSpreadsheetId();
    const meta = await sheets.spreadsheets.get({ spreadsheetId: id });
    const existing = new Map(
      (meta.data.sheets || []).map((s) => [s.properties.title, s.properties.sheetId])
    );
    const plan = planLeadTabSetup([...existing.keys()]);
    const requests = [];
    for (const { from, to } of plan.rename) {
      const sheetId = existing.get(from);
      if (sheetId == null) continue;
      requests.push({
        updateSheetProperties: {
          properties: { sheetId, title: to },
          fields: "title",
        },
      });
    }
    for (const title of plan.add) {
      requests.push({ addSheet: { properties: { title } } });
    }
    if (requests.length) {
      await sheets.spreadsheets.batchUpdate({
        spreadsheetId: id,
        requestBody: { requests },
      });
    }
    const headersWritten = [];
    for (const title of LEAD_TABS) {
      const headers = LEAD_TAB_HEADERS[title];
      const row = await sheets.spreadsheets.values.get({
        spreadsheetId: id,
        range: `${title}!1:1`,
      });
      const current = (row.data.values?.[0] || []).map((h) => String(h).trim());
      if (current.join(",") === headers.join(",")) continue;
      await sheets.spreadsheets.values.update({
        spreadsheetId: id,
        range: `${title}!A1`,
        valueInputOption: "RAW",
        requestBody: { values: [headers] },
      });
      headersWritten.push(title);
    }
    return {
      ok: true,
      spreadsheet_id: id,
      spreadsheet_title: meta.data.properties?.title || "",
      source: _resolvedSpreadsheetSource || "configured",
      renamed: plan.rename,
      added: plan.add,
      headersWritten,
    };
  } catch (err) {
    return { ok: false, error: sheetsErrorMessage(err) };
  }
}
