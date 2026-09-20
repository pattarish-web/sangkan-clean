/** Flatten / restore marketing leads for Google Sheets. Never put Ads PII extras here. */

export const LEAD_TABS = [
  "leads",
  "lead_pipeline",
  "lead_attribution",
  "lead_dashboard",
  "ads_conversions",
];

export const LEAD_HEADERS = [
  "id",
  "created_at",
  "created_date_bkk",
  "event_type",
  "contact_method",
  "clicked_target",
  "name",
  "phone",
  "service",
  "area",
  "message",
  "consent",
  "status",
  "value_thb",
  "lost_reason",
  "note",
  "page_path",
  "idempotency_key",
  "gclid",
  "channel",
  "first_channel",
  "utm_source",
  "utm_campaign",
  "keyword",
  "landing_page",
  "ads_contact_sent_at",
  "ads_qualified_sent_at",
  "ads_won_sent_at",
  "ads_order_id",
];

export const ATTR_HEADERS = [
  "lead_id",
  "gclid",
  "gbraid",
  "wbraid",
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_content",
  "utm_term",
  "campaignid",
  "adgroupid",
  "creative",
  "keyword",
  "first_channel",
  "last_channel",
  "landing_page",
  "referrer",
];

export const CONV_HEADERS = [
  "gclid",
  "conversion_name",
  "conversion_time",
  "conversion_value",
  "conversion_currency",
  "order_id",
  "upload_status",
  "uploaded_at",
  "upload_error",
];

export const PIPELINE_HEADERS = [
  "lead_id",
  "status",
  "value_thb",
  "lost_reason",
  "updated_at",
  "updated_by",
];

export const DASHBOARD_HEADERS = [
  "date_bkk",
  "leads",
  "qualified",
  "won",
  "revenue_thb",
  "google_ads",
  "facebook",
  "line",
  "organic",
  "other",
];

export const LEAD_TAB_HEADERS = {
  leads: LEAD_HEADERS,
  lead_pipeline: PIPELINE_HEADERS,
  lead_attribution: ATTR_HEADERS,
  lead_dashboard: DASHBOARD_HEADERS,
  ads_conversions: CONV_HEADERS,
};

const DEFAULT_SHEET_TITLES = new Set(["Sheet1", "Sheet 1", "ชีต1"]);

/** Plan add/rename requests from current spreadsheet titles. */
export function planLeadTabSetup(existingTitles) {
  const titles = new Set(existingTitles);
  const rename = [];
  const add = [];
  if (!titles.has("leads")) {
    const defaultTitle = [...titles].find((title) => DEFAULT_SHEET_TITLES.has(title));
    if (defaultTitle) {
      rename.push({ from: defaultTitle, to: "leads" });
      titles.delete(defaultTitle);
      titles.add("leads");
    } else {
      add.push("leads");
      titles.add("leads");
    }
  }
  for (const title of LEAD_TABS) {
    if (!titles.has(title)) add.push(title);
  }
  return { rename, add };
}

function cell(value) {
  if (value === true) return "true";
  if (value === false) return "false";
  if (value == null) return "";
  return String(value);
}

export function bangkokDate(iso) {
  try {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Bangkok",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(iso));
  } catch {
    return String(iso || "").slice(0, 10);
  }
}

export function leadToSheetRow(lead) {
  const attr = lead.attribution || {};
  const row = {};
  for (const key of LEAD_HEADERS) row[key] = "";
  row.id = lead.id || "";
  row.created_at = lead.created_at || "";
  row.created_date_bkk = lead.created_date_bkk || bangkokDate(lead.created_at);
  row.event_type = lead.event_type || (lead.contact_method === "form" ? "form_submit" : "");
  row.contact_method = lead.contact_method || "form";
  row.clicked_target = lead.clicked_target || "";
  row.name = lead.name || "";
  row.phone = lead.phone || "";
  row.service = lead.service || "";
  row.area = lead.area || "";
  row.message = lead.message || "";
  row.consent = lead.consent ? "true" : "false";
  row.status = lead.status || "new";
  row.value_thb = lead.value_thb == null ? "" : String(lead.value_thb);
  row.lost_reason = lead.lost_reason || "";
  row.note = lead.note || "";
  row.page_path = lead.page_path || "";
  row.idempotency_key = lead.idempotency_key || "";
  row.gclid = lead.gclid || attr.gclid || "";
  row.channel = attr.channel || lead.channel || "";
  row.first_channel = attr.first_channel || "";
  row.utm_source = attr.utm_source || "";
  row.utm_campaign = attr.utm_campaign || "";
  row.keyword = attr.keyword || "";
  row.landing_page = attr.landing_page || "";
  row.ads_contact_sent_at = lead.ads_contact_sent_at || "";
  row.ads_qualified_sent_at = lead.ads_qualified_sent_at || "";
  row.ads_won_sent_at = lead.ads_won_sent_at || "";
  row.ads_order_id = lead.ads_order_id || lead.id || "";
  return row;
}

export function sheetRowToLead(row) {
  const attribution = {};
  for (const key of [
    "gclid",
    "gbraid",
    "wbraid",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_term",
    "campaignid",
    "adgroupid",
    "creative",
    "keyword",
    "channel",
    "first_channel",
    "landing_page",
    "referrer",
  ]) {
    if (row[key]) attribution[key] = row[key];
  }
  const consent = String(row.consent || "") === "true";
  const valueRaw = row.value_thb;
  const value_thb =
    valueRaw === undefined || valueRaw === null || valueRaw === ""
      ? null
      : Number(valueRaw);
  return {
    id: row.id,
    created_at: row.created_at,
    created_date_bkk: row.created_date_bkk,
    event_type: row.event_type || "form_submit",
    contact_method: row.contact_method || "form",
    clicked_target: row.clicked_target || "",
    name: row.name || "",
    phone: row.phone || "",
    service: row.service || "",
    area: row.area || "",
    message: row.message || "",
    consent,
    status: row.status || "new",
    value_thb: Number.isFinite(value_thb) ? value_thb : null,
    lost_reason: row.lost_reason || "",
    note: row.note || "",
    page_path: row.page_path || "/",
    idempotency_key: row.idempotency_key || "",
    gclid: row.gclid || attribution.gclid || "",
    ads_contact_sent_at: row.ads_contact_sent_at || "",
    ads_qualified_sent_at: row.ads_qualified_sent_at || "",
    ads_won_sent_at: row.ads_won_sent_at || "",
    ads_order_id: row.ads_order_id || row.id,
    attribution,
  };
}

export function attributionToSheetRow(lead) {
  const attr = lead.attribution || {};
  const row = {};
  for (const key of ATTR_HEADERS) row[key] = "";
  row.lead_id = lead.id || "";
  for (const key of ATTR_HEADERS) {
    if (key === "lead_id") continue;
    if (key === "last_channel") {
      row[key] = attr.channel || attr.last_channel || "";
      continue;
    }
    row[key] = attr[key] || (key === "gclid" ? lead.gclid || "" : "");
  }
  return row;
}

export function conversionToSheetRow(row) {
  const out = {};
  for (const key of CONV_HEADERS) out[key] = "";
  out.gclid = row.gclid || "";
  out.conversion_name = row.conversion_name || "";
  out.conversion_time = row.conversion_time || "";
  out.conversion_value = row.conversion_value == null ? "" : String(row.conversion_value);
  out.conversion_currency = row.conversion_currency || "THB";
  out.order_id = row.order_id || "";
  out.upload_status = row.upload_status || "pending";
  out.uploaded_at = row.uploaded_at || "";
  out.upload_error = row.upload_error || "";
  return out;
}

export function sheetRowToConversion(row) {
  return {
    gclid: row.gclid || "",
    conversion_name: row.conversion_name || "",
    conversion_time: row.conversion_time || "",
    conversion_value: row.conversion_value || "",
    conversion_currency: row.conversion_currency || "THB",
    order_id: row.order_id || "",
    upload_status: row.upload_status || "pending",
    uploaded_at: row.uploaded_at || "",
    upload_error: row.upload_error || "",
  };
}

export function pickRow(headers, obj) {
  const out = {};
  for (const h of headers) out[h] = cell(obj[h]);
  return out;
}

export function summarizeLeads(leads, conversions, date) {
  const byStatus = Object.fromEntries(
    ["unverified", "new", "contacted", "qualified", "quoted", "won", "lost"].map((s) => [s, 0])
  );
  const byChannel = {};
  const byContactMethod = { phone: 0, line: 0, form: 0 };
  let revenue = 0;
  for (const lead of leads) {
    byStatus[lead.status] = (byStatus[lead.status] || 0) + 1;
    const ch = lead.attribution?.channel || "direct";
    byChannel[ch] = (byChannel[ch] || 0) + 1;
    const method = lead.contact_method || "form";
    byContactMethod[method] = (byContactMethod[method] || 0) + 1;
    if (lead.status === "won") revenue += Number(lead.value_thb || 0);
  }
  const adsUpload = { pending: 0, uploaded: 0, failed: 0 };
  for (const row of conversions || []) {
    if (row.upload_status === "uploaded") adsUpload.uploaded += 1;
    else if (row.upload_status === "failed") adsUpload.failed += 1;
    else adsUpload.pending += 1;
  }
  return {
    date: date || "all",
    total: leads.length,
    byStatus,
    byChannel,
    byContactMethod,
    revenue_thb: revenue,
    qualified: (byStatus.qualified || 0) + (byStatus.quoted || 0) + (byStatus.won || 0),
    adsUpload,
  };
}

export function memoryLeadIo() {
  const tables = {
    leads: [],
    lead_pipeline: [],
    lead_attribution: [],
    lead_dashboard: [],
    ads_conversions: [],
  };
  return {
    async readTable(name) {
      return (tables[name] || []).map((row) => ({ ...row }));
    },
    async appendRow(name, row) {
      if (!tables[name]) tables[name] = [];
      tables[name].push({ ...row });
    },
    async updateRow(name, matchFn, patch) {
      const rows = tables[name] || [];
      for (let i = 0; i < rows.length; i++) {
        if (!matchFn(rows[i])) continue;
        rows[i] = { ...rows[i], ...patch };
        return true;
      }
      return false;
    },
  };
}
