import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as line from "@line/bot-sdk";
import { getConfig } from "./config/env.js";
import { routeEvent } from "./router.js";
import { createBooking, applyAffiliateOnPayment } from "./modules/customer/index.js";
import {
  staffCheckin,
  staffUploadPow,
  listTodayJobsForStaffLineId,
} from "./modules/staff/index.js";
import {
  createBill,
  confirmPayment,
  rejectPayment,
} from "./lib/billing.js";
import { handleLeadRequest, ensureDemoSeed } from "./modules/leads/index.js";
import { serveStaticFile, shouldServeStatic } from "./lib/serveStatic.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const liffRoot = path.join(__dirname, "../../modules");

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

function sendJson(res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(body);
}

function liffInjectScript() {
  const cfg = getConfig();
  const payload = {
    LIFF_BOOKING_ID: cfg.liff.bookingId || "",
    LIFF_CHECKIN_ID: cfg.liff.checkinId || "",
    LIFF_POW_ID: cfg.liff.powId || "",
    OPS_API_BASE: "",
  };
  const assigns = Object.entries(payload)
    .map(([k, v]) => `window.${k}=${JSON.stringify(v)};`)
    .join("");
  return `<script>${assigns}</script>`;
}

async function serveLiff(res, moduleFolder, file = "index.html") {
  try {
    const fp = path.join(liffRoot, moduleFolder, file);
    let html = await readFile(fp, "utf8");
    const inject = liffInjectScript();
    if (html.includes("</head>")) {
      html = html.replace("</head>", `${inject}</head>`);
    } else {
      html = inject + html;
    }
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
  } catch {
    res.writeHead(404);
    res.end("Not found");
  }
}

async function handleApi(req, res, url) {
  if (
    req.method === "OPTIONS" &&
    !url.pathname.startsWith("/api/leads") &&
    url.pathname !== "/ops/leads"
  ) {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    });
    res.end();
    return;
  }

  if (req.method === "GET" && url.pathname === "/health") {
    const cfg = getConfig();
    sendJson(res, 200, {
      ok: true,
      service: "sangkan-office-ops",
      leads: cfg.leads.staffToken ? "enabled" : "disabled",
    });
    return;
  }

  if (req.method === "GET" && url.pathname === "/dashboard") {
    res.writeHead(302, { Location: "/ops/leads" });
    res.end();
    return;
  }

  if (await handleLeadRequest(req, res, url)) return;

  if (req.method === "GET" && url.pathname === "/liff/booking") {
    await serveLiff(res, "customer", "liff-booking.html");
    return;
  }
  if (req.method === "GET" && url.pathname === "/liff/checkin") {
    await serveLiff(res, "staff", "liff-checkin.html");
    return;
  }
  if (req.method === "GET" && url.pathname === "/liff/pow") {
    await serveLiff(res, "staff", "liff-pow.html");
    return;
  }

  if (req.method === "GET" && url.pathname === "/api/staff/today-jobs") {
    try {
      const lineUserId = url.searchParams.get("lineUserId") || "";
      const jobs = await listTodayJobsForStaffLineId(lineUserId);
      sendJson(res, 200, { ok: true, jobs });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/booking") {
    try {
      const raw = await readBody(req);
      const payload = JSON.parse(raw.toString("utf8"));
      const result = await createBooking(payload);
      sendJson(res, 200, { ok: true, ...result });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/checkin") {
    try {
      const raw = await readBody(req);
      const payload = JSON.parse(raw.toString("utf8"));
      const result = await staffCheckin(payload);
      sendJson(res, 200, { ok: true, ...result });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/pow") {
    try {
      const raw = await readBody(req);
      const payload = JSON.parse(raw.toString("utf8"));
      const result = await staffUploadPow(payload);
      sendJson(res, 200, { ok: true, ...result });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/affiliate/payment") {
    try {
      const raw = await readBody(req);
      const payload = JSON.parse(raw.toString("utf8"));
      const result = await applyAffiliateOnPayment(payload);
      sendJson(res, 200, { ok: true, result });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/billing/create") {
    try {
      const raw = await readBody(req);
      const payload = JSON.parse(raw.toString("utf8"));
      const result = await createBill(payload);
      sendJson(res, 200, { ok: true, ...result });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/billing/confirm") {
    try {
      const raw = await readBody(req);
      const payload = JSON.parse(raw.toString("utf8"));
      const result = await confirmPayment({
        ...payload,
        applyAffiliateFn: applyAffiliateOnPayment,
      });
      sendJson(res, 200, { ok: true, ...result });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/billing/reject") {
    try {
      const raw = await readBody(req);
      const payload = JSON.parse(raw.toString("utf8"));
      const result = await rejectPayment(payload);
      sendJson(res, 200, { ok: true, ...result });
    } catch (err) {
      sendJson(res, 400, { ok: false, error: err.message });
    }
    return;
  }

  // LINE webhook
  if (req.method === "POST" && (url.pathname === "/webhook" || url.pathname === "/")) {
    const cfg = getConfig();
    const raw = await readBody(req);
    const signature = req.headers["x-line-signature"];
    if (!signature || !cfg.line.channelSecret) {
      sendJson(res, 401, { error: "missing signature or secret" });
      return;
    }
    const valid = line.validateSignature(
      raw,
      cfg.line.channelSecret,
      signature
    );
    if (!valid) {
      sendJson(res, 401, { error: "invalid signature" });
      return;
    }
    const body = JSON.parse(raw.toString("utf8"));
    const events = body.events || [];
    await Promise.all(
      events.map((ev) =>
        routeEvent(ev).catch((err) => console.error("event error", err))
      )
    );
    res.writeHead(200);
    res.end("OK");
    return;
  }

  const staticRoot = getConfig().serveStaticRoot;
  if (staticRoot && shouldServeStatic(url.pathname)) {
    if (serveStaticFile(res, staticRoot, url.pathname)) return;
  }

  res.writeHead(404);
  res.end("Not found");
}

export function startServer() {
  const cfg = getConfig();
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url || "/", `http://${req.headers.host}`);
      await handleApi(req, res, url);
    } catch (err) {
      console.error(err);
      sendJson(res, 500, { error: "internal" });
    }
  });
  server.listen(cfg.port, "0.0.0.0", () => {
    console.log(`Sangkan Office ops webhook on :${cfg.port}`);
    if (cfg.serveStaticRoot) {
      console.log(`Static site + lead dashboard: http://127.0.0.1:${cfg.port}/`);
      console.log(`Daily activity report: http://127.0.0.1:${cfg.port}/ops/leads`);
    }
  });
  ensureDemoSeed().catch((err) => console.warn("lead seed:", err.message));
  return server;
}

// Long-running Node host (local / Railway / Render / Docker).
// Skip auto-listen on Vercel — vercel.json is legacy; prefer Docker deploy.
if (!process.env.VERCEL) {
  startServer();
}
