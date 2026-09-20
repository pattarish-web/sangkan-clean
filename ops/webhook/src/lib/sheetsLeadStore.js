import { newLeadId } from "./leadValidation.js";
import { conversionsToEnqueue } from "./adsConversions.js";
import {
  ATTR_HEADERS,
  CONV_HEADERS,
  LEAD_HEADERS,
  attributionToSheetRow,
  bangkokDate,
  conversionToSheetRow,
  leadToSheetRow,
  pickRow,
  sheetRowToConversion,
  sheetRowToLead,
  summarizeLeads,
} from "./leadSheetMap.js";
import { appendRow, readTable, updateRow } from "./sheets.js";

function liveIo() {
  return { readTable, appendRow, updateRow };
}

export class SheetsLeadStore {
  constructor(io = liveIo()) {
    this.io = io;
    this._lock = Promise.resolve();
  }

  withLock(fn) {
    const run = this._lock.then(fn, fn);
    this._lock = run.then(
      () => undefined,
      () => undefined
    );
    return run;
  }

  async _leads() {
    const rows = await this.io.readTable("leads");
    return rows.map(sheetRowToLead);
  }

  async create(payload, meta = {}) {
    return this.withLock(async () => {
      const leads = await this._leads();
      if (payload.idempotency_key) {
        const existing = leads.find((l) => l.idempotency_key === payload.idempotency_key);
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
      await this.io.appendRow("leads", pickRow(LEAD_HEADERS, leadToSheetRow(lead)));
      await this.io.appendRow(
        "lead_attribution",
        pickRow(ATTR_HEADERS, attributionToSheetRow(lead))
      );
      return { lead, duplicate: false };
    });
  }

  async list({ date, status, channel } = {}) {
    const leads = await this._leads();
    return leads.filter((lead) => {
      if (date && lead.created_date_bkk !== date) return false;
      if (status && lead.status !== status) return false;
      if (channel && (lead.attribution?.channel || "direct") !== channel) return false;
      return true;
    });
  }

  async get(id) {
    const leads = await this._leads();
    return leads.find((l) => l.id === id) || null;
  }

  async updateStatus(id, patch) {
    return this.withLock(async () => {
      const existing = await this.get(id);
      if (!existing) return null;
      const previous = existing.status;
      const lead = { ...existing };
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
      const ok = await this.io.updateRow(
        "leads",
        (row) => row.id === id,
        pickRow(LEAD_HEADERS, leadToSheetRow(lead))
      );
      if (!ok) return null;
      await this.io.appendRow("lead_pipeline", {
        lead_id: lead.id,
        status: lead.status,
        value_thb: lead.value_thb == null ? "" : String(lead.value_thb),
        lost_reason: lead.lost_reason || "",
        updated_at: lead.updated_at,
        updated_by: "staff",
      });
      for (const row of queued) {
        await this.io.appendRow(
          "ads_conversions",
          pickRow(
            CONV_HEADERS,
            conversionToSheetRow({
              ...row,
              upload_status: "pending",
              uploaded_at: "",
              upload_error: "",
            })
          )
        );
      }
      return { lead, queued };
    });
  }

  async conversions() {
    const rows = await this.io.readTable("ads_conversions");
    return rows.map(sheetRowToConversion);
  }

  async pendingConversions() {
    const rows = await this.conversions();
    return rows.filter((row) => row.upload_status !== "uploaded");
  }

  async markConversionUploads(updates) {
    return this.withLock(async () => {
      for (const upd of updates || []) {
        await this.io.updateRow(
          "ads_conversions",
          (row) => row.order_id === upd.order_id && row.conversion_name === upd.conversion_name,
          {
            upload_status: upd.upload_status || "",
            uploaded_at: upd.uploaded_at || "",
            upload_error: upd.upload_error || "",
          }
        );
      }
      return this.conversions();
    });
  }

  async summary(date) {
    const leads = await this.list(date ? { date } : {});
    const conversions = await this.conversions();
    const summary = summarizeLeads(leads, conversions, date);
    if (date && date !== "all") {
      const dashboard = {
        date_bkk: date,
        leads: String(summary.total),
        qualified: String(summary.qualified),
        won: String(summary.byStatus.won || 0),
        revenue_thb: String(summary.revenue_thb),
        google_ads: String(summary.byChannel.google_ads || 0),
        facebook: String(summary.byChannel.facebook || 0),
        line: String(summary.byChannel.line || 0),
        organic: String(summary.byChannel.organic || 0),
        other: String(
          summary.total -
            (summary.byChannel.google_ads || 0) -
            (summary.byChannel.facebook || 0) -
            (summary.byChannel.line || 0) -
            (summary.byChannel.organic || 0)
        ),
      };
      const updated = await this.io.updateRow(
        "lead_dashboard",
        (row) => row.date_bkk === date,
        dashboard
      );
      if (!updated) await this.io.appendRow("lead_dashboard", dashboard);
    }
    return summary;
  }

  async seedIfEmpty(rows) {
    return this.withLock(async () => {
      const leads = await this._leads();
      if (leads.length) return { seeded: false, count: leads.length };
      for (const lead of rows) {
        await this.io.appendRow("leads", pickRow(LEAD_HEADERS, leadToSheetRow(lead)));
      }
      return { seeded: true, count: rows.length };
    });
  }
}
