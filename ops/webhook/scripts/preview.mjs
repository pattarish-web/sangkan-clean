#!/usr/bin/env node
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
process.env.PORT = process.env.PORT || "43123";
process.env.SERVE_STATIC_ROOT = process.env.SERVE_STATIC_ROOT || root;
process.env.LEAD_STAFF_TOKEN = process.env.LEAD_STAFF_TOKEN || "sangkan-dev";
process.env.LEAD_SEED_DEMO = process.env.LEAD_SEED_DEMO || "1";
process.env.LEAD_STORE_FILE =
  process.env.LEAD_STORE_FILE || path.join(root, "ops/webhook/data/leads.preview.json");
process.env.LEAD_ALLOWED_ORIGINS =
  process.env.LEAD_ALLOWED_ORIGINS ||
  `http://127.0.0.1:${process.env.PORT},http://localhost:${process.env.PORT}`;
process.env.PUBLIC_BASE_URL =
  process.env.PUBLIC_BASE_URL || `http://127.0.0.1:${process.env.PORT}`;

await import("../src/index.js");
