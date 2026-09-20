import { getLeadStore } from "../../lib/leadStore.js";
import {
  validateContactClick,
  validateContactClickConfirmation,
  validateLeadCreate,
  validateStatusPatch,
} from "../../lib/leadValidation.js";
import { conversionsToCsv } from "../../lib/adsConversions.js";
import {
  adsConfigured,
  recordUploadResults,
  uploadClickConversions,
} from "../../lib/adsUpload.js";
import { clientIp, hitRateLimit } from "../../lib/rateLimit.js";
import { getConfig } from "../../config/env.js";
import { demoLeads } from "./demoData.js";
import { ensureLeadTabs } from "../../lib/sheets.js";

const MAX_BODY = 24 * 1024;

function corsHeaders(req) {
  const cfg = getConfig();
  const origin = req.headers.origin || "";
  const allowed = cfg.leads.allowedOrigins;
  const ok =
    !origin ||
    allowed.includes(origin) ||
    /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
  const headers = {
    Vary: "Origin",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Lead-Staff-Token",
  };
  if (ok && origin) headers["Access-Control-Allow-Origin"] = origin;
  return headers;
}

export function sendLeadJson(req, res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    ...corsHeaders(req),
  });
  res.end(body);
}

function staffAuthorized(req) {
  const token = getConfig().leads.staffToken;
  if (!token) return false;
  const header = String(req.headers.authorization || "");
  const bearer = header.toLowerCase().startsWith("bearer ")
    ? header.slice(7).trim()
    : "";
  const alt = String(req.headers["x-lead-staff-token"] || "").trim();
  const q = (() => {
    try {
      return new URL(req.url, "http://local").searchParams.get("token") || "";
    } catch {
      return "";
    }
  })();
  return bearer === token || alt === token || q === token;
}

async function readJson(req, res) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY) {
      sendLeadJson(req, res, 413, { ok: false, error: "payload_too_large" });
      return null;
    }
    chunks.push(chunk);
  }
  const raw = Buffer.concat(chunks).toString("utf8");
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    sendLeadJson(req, res, 400, { ok: false, error: "invalid_json" });
    return null;
  }
}

function publicLead(lead) {
  return { ok: true, id: lead.id, status: lead.status };
}

function staffLead(lead) {
  return lead;
}

export async function ensureDemoSeed() {
  const cfg = getConfig();
  if (!cfg.leads.seedDemo) return;
  const store = getLeadStore();
  await store.seedIfEmpty(demoLeads());
}

export async function handleLeadRequest(req, res, url) {
  if (req.method === "OPTIONS" && url.pathname.startsWith("/api/leads")) {
    res.writeHead(204, corsHeaders(req));
    res.end();
    return true;
  }

  if (req.method === "GET" && url.pathname === "/ops/leads") {
    const { dashboardHtml } = await import("./dashboardHtml.js");
    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
    });
    res.end(dashboardHtml());
    return true;
  }

  if (req.method === "POST" && url.pathname === "/api/leads") {
    const ip = clientIp(req);
    const ipLimit = hitRateLimit(`lead:ip:${ip}`, { limit: 8, windowMs: 10 * 60 * 1000 });
    if (!ipLimit.ok) {
      sendLeadJson(req, res, 429, { ok: false, error: "rate_limited" });
      return true;
    }
    const body = await readJson(req, res);
    if (body == null) return true;
    const parsed = validateLeadCreate(body);
    if (parsed.ignored) {
      sendLeadJson(req, res, 200, { ok: true, ignored: true });
      return true;
    }
    if (!parsed.ok) {
      sendLeadJson(req, res, parsed.status, { ok: false, error: parsed.error });
      return true;
    }
    const phoneLimit = hitRateLimit(`lead:phone:${parsed.lead.phone}`, {
      limit: 3,
      windowMs: 60 * 60 * 1000,
    });
    if (!phoneLimit.ok) {
      sendLeadJson(req, res, 429, { ok: false, error: "rate_limited" });
      return true;
    }
    const store = getLeadStore();
    const { lead, duplicate } = await store.create(parsed.lead, { ip });
    sendLeadJson(req, res, duplicate ? 200 : 201, publicLead(lead));
    return true;
  }

  if (req.method === "POST" && url.pathname === "/api/leads/contact-click") {
    const ip = clientIp(req);
    const ipLimit = hitRateLimit(`contact-click:ip:${ip}`, {
      limit: 30,
      windowMs: 10 * 60 * 1000,
    });
    if (!ipLimit.ok) {
      sendLeadJson(req, res, 429, { ok: false, error: "rate_limited" });
      return true;
    }
    const body = await readJson(req, res);
    if (body == null) return true;
    const parsed = validateContactClick(body);
    if (!parsed.ok) {
      sendLeadJson(req, res, parsed.status, { ok: false, error: parsed.error });
      return true;
    }
    const store = getLeadStore();
    const { lead, duplicate } = await store.create(parsed.lead, { ip });
    sendLeadJson(req, res, duplicate ? 200 : 201, publicLead(lead));
    return true;
  }

  if (req.method === "GET" && url.pathname === "/api/leads") {
    if (!staffAuthorized(req)) {
      sendLeadJson(req, res, 401, { ok: false, error: "unauthorized" });
      return true;
    }
    const store = getLeadStore();
    const leads = await store.list({
      date: url.searchParams.get("date") || undefined,
      status: url.searchParams.get("status") || undefined,
      channel: url.searchParams.get("channel") || undefined,
    });
    sendLeadJson(req, res, 200, { ok: true, leads: leads.map(staffLead) });
    return true;
  }

  if (req.method === "GET" && url.pathname === "/api/leads/summary") {
    if (!staffAuthorized(req)) {
      sendLeadJson(req, res, 401, { ok: false, error: "unauthorized" });
      return true;
    }
    const store = getLeadStore();
    const date = url.searchParams.get("date") || undefined;
    const summary = await store.summary(date);
    sendLeadJson(req, res, 200, { ok: true, summary });
    return true;
  }

  if (req.method === "GET" && url.pathname === "/api/leads/ads-conversions.csv") {
    if (!staffAuthorized(req)) {
      sendLeadJson(req, res, 401, { ok: false, error: "unauthorized" });
      return true;
    }
    const store = getLeadStore();
    const rows = await store.pendingConversions();
    const csv = conversionsToCsv(rows);
    res.writeHead(200, {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": "attachment; filename=sangkan-ads-conversions.csv",
      "Cache-Control": "no-store",
    });
    res.end(csv);
    return true;
  }

  const patchMatch = url.pathname.match(/^\/api\/leads\/([^/]+)$/);
  if (req.method === "PATCH" && patchMatch) {
    if (!staffAuthorized(req)) {
      sendLeadJson(req, res, 401, { ok: false, error: "unauthorized" });
      return true;
    }
    const body = await readJson(req, res);
    if (body == null) return true;
    const parsed = validateStatusPatch(body);
    if (!parsed.ok) {
      sendLeadJson(req, res, parsed.status, { ok: false, error: parsed.error });
      return true;
    }
    const store = getLeadStore();
    const id = decodeURIComponent(patchMatch[1]);
    const existing = await store.get(id);
    if (!existing) {
      sendLeadJson(req, res, 404, { ok: false, error: "not_found" });
      return true;
    }
    const confirm = validateContactClickConfirmation(existing, parsed.patch);
    if (!confirm.ok) {
      sendLeadJson(req, res, confirm.status, { ok: false, error: confirm.error });
      return true;
    }
    const result = await store.updateStatus(id, parsed.patch);
    if (!result) {
      sendLeadJson(req, res, 404, { ok: false, error: "not_found" });
      return true;
    }
    let ads_upload = { skipped: true, reason: "empty", uploaded: 0, failed: 0 };
    if (result.queued.length) {
      ads_upload = await recordUploadResults(
        store,
        await uploadClickConversions(result.queued.map((row) => ({ ...row, upload_status: "pending" })))
      );
    }
    sendLeadJson(req, res, 200, {
      ok: true,
      lead: result.lead,
      queued_conversions: result.queued.length,
      ads_upload: {
        skipped: Boolean(ads_upload.skipped),
        reason: ads_upload.reason || "",
        uploaded: ads_upload.uploaded || 0,
        failed: ads_upload.failed || 0,
      },
    });
    return true;
  }

  if (req.method === "POST" && url.pathname === "/api/leads/setup-tabs") {
    if (!staffAuthorized(req)) {
      sendLeadJson(req, res, 401, { ok: false, error: "unauthorized" });
      return true;
    }
    const result = await ensureLeadTabs();
    sendLeadJson(req, res, result.ok ? 200 : 503, result);
    return true;
  }

  if (req.method === "POST" && url.pathname === "/api/leads/ads-conversions/upload") {
    if (!staffAuthorized(req)) {
      sendLeadJson(req, res, 401, { ok: false, error: "unauthorized" });
      return true;
    }
    const store = getLeadStore();
    const pending = await store.pendingConversions();
    const ads_upload = await recordUploadResults(store, await uploadClickConversions(pending));
    sendLeadJson(req, res, 200, {
      ok: true,
      configured: adsConfigured(),
      pending: pending.length,
      ads_upload: {
        skipped: Boolean(ads_upload.skipped),
        reason: ads_upload.reason || "",
        uploaded: ads_upload.uploaded || 0,
        failed: ads_upload.failed || 0,
      },
    });
    return true;
  }

  return false;
}
