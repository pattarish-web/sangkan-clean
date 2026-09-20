/** Upload staff-confirmed conversions to Google Ads. Never send PII. */

const DEFAULT_CUSTOMER_ID = "6151208199";
const DEFAULT_LOGIN_CUSTOMER_ID = "7915729299";
const DEFAULT_API_VERSION = "v19";
const ACTION_NAMES = ["phone_click", "line_click", "qualified_lead", "won_deal"];

let _fetchImpl = globalThis.fetch.bind(globalThis);
let _configOverride = null;
let _tokenCache = { accessToken: "", expiresAt: 0 };
let _actionCache = { at: 0, map: null };

export function setAdsFetch(fn) {
  _fetchImpl = fn || globalThis.fetch.bind(globalThis);
}

export function setAdsConfigOverride(cfg) {
  _configOverride = cfg;
  _tokenCache = { accessToken: "", expiresAt: 0 };
  _actionCache = { at: 0, map: null };
}

export function adsDateTime(iso) {
  if (!iso) return "";
  let s = String(iso).trim();
  s = s.replace("T", " ").replace(/\.\d{3}/, "");
  if (s.endsWith("Z")) s = s.slice(0, -1) + "+00:00";
  return s;
}

export function clickConversionBody(row, actionResource) {
  const body = {
    gclid: String(row.gclid || ""),
    conversionAction: actionResource,
    conversionDateTime: adsDateTime(row.conversion_time),
    currencyCode: String(row.conversion_currency || "THB"),
    orderId: String(row.order_id || ""),
  };
  const value = Number(row.conversion_value);
  if (Number.isFinite(value) && value > 0) body.conversionValue = value;
  return body;
}

export function payloadHasPii(payload) {
  const blob = JSON.stringify(payload);
  if (/"name"|"phone"|"email"|"message"/.test(blob)) return true;
  return /0[1-9]\d{8}/.test(blob);
}

export function readAdsConfig() {
  if (_configOverride) return _configOverride;
  return {
    developerToken: process.env.GOOGLE_ADS_DEVELOPER_TOKEN || "",
    clientId: process.env.GOOGLE_ADS_CLIENT_ID || "",
    clientSecret: process.env.GOOGLE_ADS_CLIENT_SECRET || "",
    refreshToken: process.env.GOOGLE_ADS_REFRESH_TOKEN || "",
    customerId: String(process.env.GOOGLE_ADS_TARGET_CUSTOMER_ID || DEFAULT_CUSTOMER_ID).replace(/-/g, ""),
    loginCustomerId: String(process.env.GOOGLE_ADS_LOGIN_CUSTOMER_ID || DEFAULT_LOGIN_CUSTOMER_ID).replace(/-/g, ""),
    apiVersion: process.env.GOOGLE_ADS_API_VERSION || DEFAULT_API_VERSION,
  };
}

export function adsConfigured(cfg = readAdsConfig()) {
  return Boolean(cfg.clientId && cfg.clientSecret && cfg.refreshToken);
}

function adsHeaders(cfg, accessToken) {
  const headers = {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
  };
  if (cfg.developerToken) {
    headers["developer-token"] = cfg.developerToken;
  }
  if (cfg.loginCustomerId && cfg.loginCustomerId !== cfg.customerId) {
    headers["login-customer-id"] = cfg.loginCustomerId;
  }
  return headers;
}

async function readJsonResponse(res) {
  const text = await res.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return { error: { message: text.slice(0, 200) } };
  }
}

async function accessToken(cfg) {
  const now = Date.now();
  if (_tokenCache.accessToken && _tokenCache.expiresAt > now + 30_000) {
    return _tokenCache.accessToken;
  }
  const body = new URLSearchParams({
    client_id: cfg.clientId,
    client_secret: cfg.clientSecret,
    refresh_token: cfg.refreshToken,
    grant_type: "refresh_token",
  });
  const res = await _fetchImpl("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const json = await readJsonResponse(res);
  if (!res.ok || !json.access_token) {
    throw new Error("ads_oauth_failed");
  }
  _tokenCache = {
    accessToken: json.access_token,
    expiresAt: now + Number(json.expires_in || 3500) * 1000,
  };
  return _tokenCache.accessToken;
}

async function conversionActionMap(cfg, token) {
  const now = Date.now();
  if (_actionCache.map && now - _actionCache.at < 60 * 60 * 1000) return _actionCache.map;
  const names = ACTION_NAMES.map((n) => `'${n}'`).join(", ");
  const res = await _fetchImpl(
    `https://googleads.googleapis.com/${cfg.apiVersion}/customers/${cfg.customerId}/googleAds:search`,
    {
      method: "POST",
      headers: adsHeaders(cfg, token),
      body: JSON.stringify({
        query: `SELECT conversion_action.resource_name, conversion_action.name FROM conversion_action WHERE conversion_action.name IN (${names}) AND conversion_action.status != 'REMOVED'`,
      }),
    }
  );
  const json = await readJsonResponse(res);
  if (!res.ok) throw new Error("ads_action_lookup_failed");
  const map = {};
  for (const row of json.results || []) {
    const action = row.conversionAction || row.conversion_action || {};
    if (action.name && (action.resourceName || action.resource_name)) {
      map[action.name] = action.resourceName || action.resource_name;
    }
  }
  _actionCache = { at: now, map };
  return map;
}

function publicUploadResult(row, status, error) {
  return {
    order_id: row.order_id,
    conversion_name: row.conversion_name,
    upload_status: status,
    upload_error: error || "",
    uploaded_at: status === "uploaded" ? new Date().toISOString() : "",
  };
}

/**
 * Upload queued conversion rows. Input/output never include name/phone/message.
 */
export async function uploadClickConversions(rows) {
  const pending = (rows || []).filter(
    (row) => row && row.gclid && row.conversion_name && row.upload_status !== "uploaded"
  );
  const cfg = readAdsConfig();
  if (!pending.length) {
    return { ok: true, uploaded: 0, failed: 0, skipped: true, reason: "empty", results: [] };
  }
  if (!adsConfigured(cfg)) {
    return {
      ok: true,
      uploaded: 0,
      failed: 0,
      skipped: true,
      reason: "not_configured",
      results: pending.map((row) => publicUploadResult(row, "pending", "not_configured")),
    };
  }

  try {
    const token = await accessToken(cfg);
    const actions = await conversionActionMap(cfg, token);
    const conversions = [];
    const indexMap = [];
    const results = [];
    for (const row of pending) {
      const resource = actions[row.conversion_name];
      if (!resource) {
        results.push(publicUploadResult(row, "failed", `missing_action:${row.conversion_name}`));
        continue;
      }
      conversions.push(clickConversionBody(row, resource));
      indexMap.push(row);
    }
    if (!conversions.length) {
      return { ok: false, uploaded: 0, failed: results.length, skipped: false, results };
    }
    if (payloadHasPii(conversions)) {
      const failed = pending.map((row) => publicUploadResult(row, "failed", "pii_blocked"));
      return { ok: false, uploaded: 0, failed: failed.length, skipped: false, results: failed };
    }
    const res = await _fetchImpl(
      `https://googleads.googleapis.com/${cfg.apiVersion}/customers/${cfg.customerId}:uploadClickConversions`,
      {
        method: "POST",
        headers: adsHeaders(cfg, token),
        body: JSON.stringify({ conversions, partialFailure: true }),
      }
    );
    const json = await readJsonResponse(res);
    if (!res.ok && !json.results) {
      const failed = pending.map((row) => publicUploadResult(row, "failed", "ads_upload_http"));
      return { ok: false, uploaded: 0, failed: failed.length, skipped: false, results: failed };
    }
    const apiResults = json.results || [];
    for (let i = 0; i < indexMap.length; i++) {
      const row = indexMap[i];
      const item = apiResults[i] || {};
      if (Object.keys(item).length === 0) {
        results.push(publicUploadResult(row, "failed", "partial_failure"));
      } else {
        results.push(publicUploadResult(row, "uploaded"));
      }
    }
    const uploaded = results.filter((r) => r.upload_status === "uploaded").length;
    const failed = results.filter((r) => r.upload_status === "failed").length;
    return { ok: failed === 0, uploaded, failed, skipped: false, results };
  } catch (err) {
    const reason = err && err.message ? String(err.message).slice(0, 80) : "ads_upload_failed";
    return {
      ok: false,
      uploaded: 0,
      failed: pending.length,
      skipped: false,
      results: pending.map((row) => publicUploadResult(row, "failed", reason)),
    };
  }
}

export async function recordUploadResults(store, upload) {
  if (!store || !upload?.results?.length) return upload;
  await store.markConversionUploads(upload.results);
  return upload;
}
