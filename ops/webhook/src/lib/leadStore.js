import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { newLeadId } from "./leadValidation.js";
import { conversionsToEnqueue } from "./adsConversions.js";
import { bangkokDate, summarizeLeads } from "./leadSheetMap.js";
import { SheetsLeadStore } from "./sheetsLeadStore.js";
import { getConfig } from "../config/env.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const defaultFile = path.join(__dirname, "../../data/leads.json");

function emptyState() {
  return { leads: [], conversions: [] };
}

export class FileLeadStore {
  constructor(filePath = process.env.LEAD_STORE_FILE || defaultFile) {
    this.filePath = filePath;
    this._state = null;
    this._lock = Promise.resolve();
  }

  async _load() {
    if (this._state) return this._state;
    try {
      const raw = await readFile(this.filePath, "utf8");
      this._state = JSON.parse(raw);
      if (!Array.isArray(this._state.leads)) this._state.leads = [];
      if (!Array.isArray(this._state.conversions)) this._state.conversions = [];
    } catch {
      this._state = emptyState();
    }
    return this._state;
  }

  async _save() {
    await mkdir(path.dirname(this.filePath), { recursive: true });
    const tmp = `${this.filePath}.${process.pid}.tmp`;
    await writeFile(tmp, JSON.stringify(this._state, null, 2), "utf8");
    await writeFile(this.filePath, JSON.stringify(this._state, null, 2), "utf8");
  }

  withLock(fn) {
    const run = this._lock.then(fn, fn);
    this._lock = run.then(
      () => undefined,
      () => undefined
    );
    return run;
  }

  async create(payload, meta = {}) {
    return this.withLock(async () => {
      const state = await this._load();
      if (payload.idempotency_key) {
        const existing = state.leads.find(
          (l) => l.idempotency_key === payload.idempotency_key
        );
        if (existing) return { lead: existing, duplicate: true };
      }
      const created_at = new Date().toISOString();
      const lead = {
        id: newLeadId(new Date()),
        status: "new",
        value_thb: null,
        lost_reason: "",
        note: "",
        created_at,
        updated_at: created_at,
        created_date_bkk: bangkokDate(created_at),
        ads_contact_sent_at: "",
        ads_qualified_sent_at: "",
        ads_won_sent_at: "",
        ads_order_id: "",
        source_ip: meta.ip || "",
        contact_method: "form",
        event_type: "form_submit",
        ...payload,
        gclid: payload.attribution?.gclid || "",
      };
      lead.ads_order_id = lead.id;
      state.leads.unshift(lead);
      await this._save();
      return { lead, duplicate: false };
    });
  }

  async list({ date, status, channel } = {}) {
    const state = await this._load();
    return state.leads.filter((lead) => {
      if (date && lead.created_date_bkk !== date) return false;
      if (status && lead.status !== status) return false;
      if (channel && (lead.attribution?.channel || "direct") !== channel) return false;
      return true;
    });
  }

  async get(id) {
    const state = await this._load();
    return state.leads.find((l) => l.id === id) || null;
  }

  async updateStatus(id, patch) {
    return this.withLock(async () => {
      const state = await this._load();
      const lead = state.leads.find((l) => l.id === id);
      if (!lead) return null;
      const previous = lead.status;
      lead.status = patch.status;
      if (patch.value_thb != null) lead.value_thb = patch.value_thb;
      if (patch.lost_reason != null) lead.lost_reason = patch.lost_reason;
      if (patch.note != null) lead.note = patch.note;
      if (patch.name != null) lead.name = patch.name;
      if (patch.phone != null) lead.phone = patch.phone;
      if (patch.service != null) lead.service = patch.service;
      if (patch.area != null) lead.area = patch.area;
      lead.updated_at = new Date().toISOString();
      const queued = conversionsToEnqueue(lead, previous);
      for (const row of queued) {
        state.conversions.push({
          ...row,
          queued_at: lead.updated_at,
          upload_status: "pending",
          uploaded_at: "",
          upload_error: "",
        });
        if (row.conversion_name === "phone_click" || row.conversion_name === "line_click") {
          lead.ads_contact_sent_at = lead.updated_at;
        }
        if (row.conversion_name === "qualified_lead") {
          lead.ads_qualified_sent_at = lead.updated_at;
        }
        if (row.conversion_name === "won_deal") {
          lead.ads_won_sent_at = lead.updated_at;
        }
      }
      await this._save();
      return { lead, queued };
    });
  }

  async conversions() {
    const state = await this._load();
    return state.conversions;
  }

  async pendingConversions() {
    const state = await this._load();
    return state.conversions.filter((row) => row.upload_status !== "uploaded");
  }

  async markConversionUploads(updates) {
    return this.withLock(async () => {
      const state = await this._load();
      for (const upd of updates || []) {
        const row = state.conversions.find(
          (c) => c.order_id === upd.order_id && c.conversion_name === upd.conversion_name
        );
        if (!row) continue;
        row.upload_status = upd.upload_status || row.upload_status;
        if (upd.uploaded_at != null) row.uploaded_at = upd.uploaded_at;
        if (upd.upload_error != null) row.upload_error = upd.upload_error;
      }
      await this._save();
      return state.conversions;
    });
  }

  async summary(date) {
    const leads = await this.list(date ? { date } : {});
    const state = await this._load();
    return summarizeLeads(leads, state.conversions, date);
  }

  async seedIfEmpty(rows) {
    return this.withLock(async () => {
      const state = await this._load();
      if (state.leads.length) return { seeded: false, count: state.leads.length };
      state.leads = rows;
      state.conversions = [];
      await this._save();
      return { seeded: true, count: rows.length };
    });
  }
}

export function sheetsLeadStoreEnabled() {
  try {
    const cfg = getConfig();
    if (cfg.leads.storeFile) return false;
    return Boolean(cfg.sheets.spreadsheetId && cfg.sheets.serviceAccountJson);
  } catch {
    return false;
  }
}

let _store;
export function getLeadStore() {
  if (_store) return _store;
  const cfg = getConfig();
  if (cfg.leads.storeFile) {
    _store = new FileLeadStore(cfg.leads.storeFile);
    return _store;
  }
  if (sheetsLeadStoreEnabled()) {
    _store = new SheetsLeadStore();
    return _store;
  }
  _store = new FileLeadStore();
  return _store;
}

export function setLeadStore(store) {
  _store = store;
}
