export const PIPELINE_STATUSES = [
  "unverified",
  "new",
  "contacted",
  "qualified",
  "quoted",
  "won",
  "lost",
];

/** Statuses that mean staff confirmed a real customer — safe to send to Google Ads. */
export const CONFIRMED_ADS_STATUSES = [
  "new",
  "contacted",
  "qualified",
  "quoted",
  "won",
];

export function contactMethodOf(lead) {
  if (lead?.contact_method === "phone" || lead?.contact_method === "line") {
    return lead.contact_method;
  }
  if (lead?.event_type === "phone_click") return "phone";
  if (lead?.event_type === "line_click") return "line";
  return "";
}

export const SERVICES = [
  "Big Cleaning",
  "Sangkan Office",
  "แม่บ้านประจำ",
  "ทำความสะอาดทั่วไป",
  "หลังก่อสร้าง",
  "อื่นๆ",
];

const ATTR_KEYS = [
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
  "first_utm_source",
  "first_utm_medium",
  "first_utm_campaign",
  "first_gclid",
  "first_landing_page",
  "last_utm_source",
  "last_utm_campaign",
  "last_gclid",
];

const MAX_TEXT = {
  name: 80,
  phone: 32,
  service: 80,
  area: 120,
  message: 2000,
  page_path: 180,
  idempotency_key: 80,
};

export function normalizePhone(raw) {
  const digits = String(raw || "").replace(/\D/g, "");
  if (digits.startsWith("66") && digits.length >= 11) {
    return "0" + digits.slice(2, 11);
  }
  if (digits.length === 10 && digits.startsWith("0")) return digits;
  if (digits.length === 9) return "0" + digits;
  return digits;
}

export function isThaiMobile(phone) {
  return /^0[1-9]\d{8}$/.test(phone);
}

function clip(value, max) {
  return String(value || "").trim().slice(0, max);
}

export function sanitizeAttribution(input) {
  const src = input && typeof input === "object" ? input : {};
  const out = {};
  for (const key of ATTR_KEYS) {
    if (src[key] == null || src[key] === "") continue;
    out[key] = String(src[key]).trim().slice(0, 180);
  }
  return out;
}

/**
 * Validate a public lead create payload.
 * Returns { ok:true, lead } or { ok:false, error, status }.
 * Honeypot hits return ok:true with { ignored:true }.
 */
export function validateLeadCreate(body) {
  if (!body || typeof body !== "object") {
    return { ok: false, status: 400, error: "invalid_json" };
  }
  if (String(body.honeypot || body.company_website || "").trim()) {
    return { ok: true, ignored: true };
  }
  const name = clip(body.name, MAX_TEXT.name);
  const phone = normalizePhone(body.phone);
  const service = clip(body.service, MAX_TEXT.service);
  const area = clip(body.area, MAX_TEXT.area);
  const message = clip(body.message, MAX_TEXT.message);
  const consent = body.consent === true || body.consent === "true" || body.consent === "on";

  if (name.length < 2) return { ok: false, status: 400, error: "name_required" };
  if (!isThaiMobile(phone)) return { ok: false, status: 400, error: "phone_invalid" };
  if (!service) return { ok: false, status: 400, error: "service_required" };
  if (!consent) return { ok: false, status: 400, error: "consent_required" };

  return {
    ok: true,
    lead: {
      name,
      phone,
      service,
      area,
      message,
      consent: true,
      contact_method: "form",
      event_type: "form_submit",
      page_path: clip(body.page_path, MAX_TEXT.page_path) || "/",
      idempotency_key: clip(body.idempotency_key, MAX_TEXT.idempotency_key),
      attribution: sanitizeAttribution(body.attribution),
    },
  };
}

/** Validate a phone/LINE click. This contains attribution only, never customer PII. */
export function validateContactClick(body) {
  if (!body || typeof body !== "object") {
    return { ok: false, status: 400, error: "invalid_json" };
  }
  const contact_method = clip(body.contact_method, 16);
  if (!["phone", "line"].includes(contact_method)) {
    return { ok: false, status: 400, error: "contact_method_invalid" };
  }
  return {
    ok: true,
    lead: {
      name: "",
      phone: "",
      service: contact_method === "phone" ? "คลิกโทรจากเว็บไซต์" : "คลิก LINE จากเว็บไซต์",
      area: "",
      message: "",
      consent: false,
      status: "unverified",
      event_type: `${contact_method}_click`,
      contact_method,
      clicked_target: clip(body.clicked_target, 180),
      page_path: clip(body.page_path, MAX_TEXT.page_path) || "/",
      idempotency_key: clip(body.idempotency_key, MAX_TEXT.idempotency_key),
      attribution: sanitizeAttribution(body.attribution),
    },
  };
}

export function validateStatusPatch(body) {
  if (!body || typeof body !== "object") {
    return { ok: false, status: 400, error: "invalid_json" };
  }
  const status = String(body.status || "").trim();
  if (!PIPELINE_STATUSES.includes(status)) {
    return { ok: false, status: 400, error: "status_invalid" };
  }
  const valueRaw = body.value_thb;
  const value_thb =
    valueRaw === undefined || valueRaw === null || valueRaw === ""
      ? null
      : Number(valueRaw);
  if (value_thb != null && (!Number.isFinite(value_thb) || value_thb < 0)) {
    return { ok: false, status: 400, error: "value_invalid" };
  }
  if (status === "won" && !(value_thb > 0)) {
    return { ok: false, status: 400, error: "won_requires_value" };
  }
  const lost_reason = clip(body.lost_reason, 180);
  const note = clip(body.note, 500);
  const patch = { status, value_thb, lost_reason, note };
  if (Object.hasOwn(body, "name")) patch.name = clip(body.name, MAX_TEXT.name);
  if (Object.hasOwn(body, "phone")) {
    const phone = normalizePhone(body.phone);
    if (phone && !isThaiMobile(phone)) {
      return { ok: false, status: 400, error: "phone_invalid" };
    }
    patch.phone = phone;
  }
  if (Object.hasOwn(body, "service")) patch.service = clip(body.service, MAX_TEXT.service);
  if (Object.hasOwn(body, "area")) patch.area = clip(body.area, MAX_TEXT.area);
  return { ok: true, patch };
}

/**
 * Phone/LINE clicks may only leave "รอตรวจสอบ" into a confirmed status
 * after staff fills the customer name and phone from call/chat history.
 * Lost and remaining unverified do not send Google Ads conversions.
 */
export function validateContactClickConfirmation(existing, patch) {
  if (!existing || !patch) return { ok: true };
  const method = contactMethodOf(existing) || contactMethodOf(patch);
  if (!method) return { ok: true };
  if (!CONFIRMED_ADS_STATUSES.includes(patch.status)) return { ok: true };
  const name = Object.hasOwn(patch, "name") ? patch.name : existing.name;
  const phone = Object.hasOwn(patch, "phone") ? patch.phone : existing.phone;
  if (String(name || "").trim().length < 2) {
    return { ok: false, status: 400, error: "confirm_name_required" };
  }
  if (!isThaiMobile(normalizePhone(phone))) {
    return { ok: false, status: 400, error: "confirm_phone_required" };
  }
  return { ok: true };
}

/** Payload Google Ads is allowed to receive — never name/phone/email/message. */
export function adsSafeConversionRow(lead, conversionName, occurredAtIso) {
  return {
    gclid: lead.gclid || lead.attribution?.gclid || "",
    conversion_name: conversionName,
    conversion_time: occurredAtIso,
    conversion_value: conversionName === "won_deal" ? Number(lead.value_thb || 0) : "",
    conversion_currency: "THB",
    order_id: lead.ads_order_id || lead.id,
  };
}

export function newLeadId(date = new Date()) {
  const y = date.toISOString().slice(0, 10).replace(/-/g, "");
  const r = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `LD-${y}-${r}`;
}
