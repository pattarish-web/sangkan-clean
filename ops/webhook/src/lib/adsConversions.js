import { adsSafeConversionRow, contactMethodOf, CONFIRMED_ADS_STATUSES } from "./leadValidation.js";

const QUALIFIED = "qualified_lead";
const WON = "won_deal";
const PHONE = "phone_click";
const LINE = "line_click";
const CONFIRMED = new Set(CONFIRMED_ADS_STATUSES);

function isoNow() {
  return toAdsTime(new Date().toISOString());
}

function toAdsTime(iso) {
  const raw = iso || new Date().toISOString();
  return String(raw).replace(/\.\d{3}Z$/, "+00:00").replace(/Z$/, "+00:00");
}

function gclidOf(lead) {
  return lead.gclid || lead.attribution?.gclid || "";
}

function contactConversionName(method) {
  if (method === "phone") return PHONE;
  if (method === "line") return LINE;
  return "";
}

/**
 * Decide which Google Ads offline conversions to enqueue after a status change.
 * Phone/LINE clicks wait until staff confirms (leaves unverified/lost).
 * Never includes PII. Won requires value > 0. Each conversion fires at most once.
 */
export function conversionsToEnqueue(lead, previousStatus) {
  const rows = [];
  const gclid = gclidOf(lead);
  if (!gclid) return rows;
  const status = lead.status;
  const method = contactMethodOf(lead);
  const contactName = contactConversionName(method);
  if (
    contactName &&
    CONFIRMED.has(status) &&
    !CONFIRMED.has(previousStatus) &&
    !lead.ads_contact_sent_at
  ) {
    rows.push(adsSafeConversionRow(lead, contactName, toAdsTime(lead.created_at)));
  }
  if (
    (status === "qualified" || status === "quoted" || status === "won") &&
    previousStatus !== "qualified" &&
    previousStatus !== "quoted" &&
    previousStatus !== "won" &&
    !lead.ads_qualified_sent_at
  ) {
    rows.push(adsSafeConversionRow(lead, QUALIFIED, isoNow()));
  }
  if (status === "won" && !lead.ads_won_sent_at && Number(lead.value_thb) > 0) {
    rows.push(adsSafeConversionRow(lead, WON, isoNow()));
  }
  return rows;
}

export function csvEscape(value) {
  const s = value == null ? "" : String(value);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function conversionsToCsv(rows) {
  const header = [
    "Google Click ID",
    "Conversion Name",
    "Conversion Time",
    "Conversion Value",
    "Conversion Currency",
    "Order ID",
  ];
  const lines = [header.join(",")];
  for (const row of rows) {
    lines.push(
      [
        csvEscape(row.gclid),
        csvEscape(row.conversion_name),
        csvEscape(row.conversion_time),
        csvEscape(row.conversion_value),
        csvEscape(row.conversion_currency),
        csvEscape(row.order_id),
      ].join(",")
    );
  }
  return lines.join("\n") + "\n";
}

export const CONVERSION_NAMES = { QUALIFIED, WON, PHONE, LINE };
