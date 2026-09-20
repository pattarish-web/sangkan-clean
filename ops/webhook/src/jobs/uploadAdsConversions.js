#!/usr/bin/env node
import { getLeadStore } from "../lib/leadStore.js";
import { adsConfigured, recordUploadResults, uploadClickConversions } from "../lib/adsUpload.js";

const store = getLeadStore();
const pending = await store.pendingConversions();
const result = await recordUploadResults(store, await uploadClickConversions(pending));
const summary = {
  ok: Boolean(result.ok || result.skipped),
  configured: adsConfigured(),
  pending: pending.length,
  uploaded: result.uploaded || 0,
  failed: result.failed || 0,
  skipped: Boolean(result.skipped),
  reason: result.reason || "",
};
console.log(JSON.stringify(summary));
if (result.failed) process.exitCode = 1;
