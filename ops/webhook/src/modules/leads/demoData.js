import { newLeadId } from "../../lib/leadValidation.js";

function isoHoursAgo(hours) {
  return new Date(Date.now() - hours * 3600 * 1000).toISOString();
}

function bkkDate(iso) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Bangkok",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(iso));
}

function row(partial) {
  const created_at = partial.created_at || new Date().toISOString();
  const id = partial.id || newLeadId(new Date(created_at));
  return {
    status: "new",
    value_thb: null,
    lost_reason: "",
    note: "",
    consent: true,
    page_path: "/",
    idempotency_key: "",
    ads_contact_sent_at: "",
    ads_qualified_sent_at: "",
    ads_won_sent_at: "",
    source_ip: "demo",
    gclid: partial.attribution?.gclid || "",
    ads_order_id: id,
    updated_at: created_at,
    created_date_bkk: bkkDate(created_at),
    ...partial,
    id,
    created_at,
  };
}

/** Sample leads for local preview — fictional contacts only. */
export function demoLeads() {
  const now = Date.now();
  const t0 = new Date(now - 8 * 60 * 1000).toISOString();
  const t1 = new Date(now - 18 * 60 * 1000).toISOString();
  const t2 = new Date(now - 32 * 60 * 1000).toISOString();
  const t3 = new Date(now - 26 * 3600 * 1000).toISOString();
  const t4 = new Date(now - 28 * 3600 * 1000).toISOString();
  const t5 = new Date(now - 30 * 3600 * 1000).toISOString();
  return [
    row({
      id: "LD-DEMO-001",
      name: "สมชาย วงศ์สะอาด",
      phone: "0812345678",
      service: "Big Cleaning",
      area: "บางนา กรุงเทพฯ",
      message: "บ้าน 2 ชั้น หลังก่อสร้าง อยากให้เข้างานวันเสาร์",
      status: "new",
      created_at: t0,
      attribution: {
        channel: "google_ads",
        first_channel: "google_ads",
        gclid: "CjwKCAjw-demo-gclid-001",
        utm_source: "google",
        utm_medium: "cpc",
        utm_campaign: "SK-BigClean-Search",
        utm_content: "BC-Core",
        keyword: "รับทำความสะอาดบ้าน",
        campaignid: "123001",
        adgroupid: "456001",
        landing_page: "/landing-bigcleaning.html",
      },
      gclid: "CjwKCAjw-demo-gclid-001",
    }),
    row({
      id: "LD-DEMO-002",
      name: "วิภา ศรีสุข",
      phone: "0891112233",
      service: "แม่บ้านประจำ",
      area: "พระโขนง",
      message: "ออฟฟิศ 120 ตร.ม. ต้องการแม่บ้าน 3 วัน/สัปดาห์",
      status: "contacted",
      note: "โทรแล้ว นัดคุยต่อพรุ่งนี้",
      created_at: t1,
      attribution: {
        channel: "facebook",
        first_channel: "facebook",
        fbclid: "fbclid-demo-002",
        utm_source: "facebook",
        utm_medium: "paid",
        utm_campaign: "maid-awareness",
        landing_page: "/landing-maid.html",
      },
    }),
    row({
      id: "LD-DEMO-003",
      name: "ปรีชา ทองดี",
      phone: "0625550102",
      service: "Big Cleaning",
      area: "ลาดพร้าว",
      message: "คอนโด 1 ห้องนอน ก่อนย้ายเข้า",
      status: "qualified",
      created_at: t2,
      ads_qualified_sent_at: t2,
      attribution: {
        channel: "google_ads",
        first_channel: "google_ads",
        gclid: "CjwKCAjw-demo-gclid-003",
        utm_source: "google",
        utm_medium: "cpc",
        utm_campaign: "SK-BigClean-Search",
        keyword: "big cleaning คอนโด",
        landing_page: "/landing-bigcleaning.html",
      },
      gclid: "CjwKCAjw-demo-gclid-003",
    }),
    row({
      id: "LD-DEMO-004",
      name: "บริษัท เอบีซี จำกัด",
      phone: "021112233",
      service: "ทำความสะอาดทั่วไป",
      area: "อโศก",
      message: "สำนักงาน 8 ชั้น ขอใบเสนอราคารายเดือน",
      status: "quoted",
      created_at: t3,
      attribution: {
        channel: "organic",
        first_channel: "organic",
        utm_source: "google",
        utm_medium: "organic",
        referrer: "www.google.com",
        landing_page: "/",
      },
    }),
    row({
      id: "LD-DEMO-005",
      name: "นิดา บุญมา",
      phone: "0839988776",
      service: "Big Cleaning",
      area: "ราชพฤกษ์",
      message: "บ้านเดี่ยว ปิดงานแล้ว",
      status: "won",
      value_thb: 18500,
      created_at: t4,
      ads_qualified_sent_at: t4,
      ads_won_sent_at: t4,
      attribution: {
        channel: "google_ads",
        first_channel: "google_ads",
        gclid: "CjwKCAjw-demo-gclid-005",
        utm_source: "google",
        utm_medium: "cpc",
        utm_campaign: "SK-BigClean-Search",
        keyword: "ทำความสะอาดบ้านเดี่ยว",
        landing_page: "/index.html",
      },
      gclid: "CjwKCAjw-demo-gclid-005",
    }),
    row({
      id: "LD-DEMO-007",
      name: "",
      phone: "",
      service: "คลิกโทรจากเว็บไซต์",
      status: "unverified",
      event_type: "phone_click",
      contact_method: "phone",
      consent: false,
      created_at: t0,
      attribution: {
        channel: "google_ads",
        first_channel: "google_ads",
        gclid: "CjwKCAjw-demo-gclid-007",
        utm_source: "google",
        utm_medium: "cpc",
        utm_campaign: "SK-BigClean-Search",
        keyword: "รับทำความสะอาดบ้าน",
        landing_page: "/landing-bigcleaning.html",
      },
      gclid: "CjwKCAjw-demo-gclid-007",
    }),
    row({
      id: "LD-DEMO-008",
      name: "",
      phone: "",
      service: "คลิก LINE จากเว็บไซต์",
      status: "unverified",
      event_type: "line_click",
      contact_method: "line",
      consent: false,
      created_at: t1,
      attribution: {
        channel: "google_ads",
        first_channel: "google_ads",
        gclid: "CjwKCAjw-demo-gclid-008",
        utm_source: "google",
        utm_medium: "cpc",
        utm_campaign: "SK-BigClean-Search",
        landing_page: "/",
      },
      gclid: "CjwKCAjw-demo-gclid-008",
    }),
    row({
      id: "LD-DEMO-006",
      name: "มานะ ใจดี",
      phone: "0867001122",
      service: "อื่นๆ",
      area: "สมุทรปราการ",
      message: "ขอราคาอบโอโซน",
      status: "lost",
      lost_reason: "งบไม่ตรง",
      created_at: t5,
      attribution: {
        channel: "line",
        first_channel: "line",
        utm_source: "line",
        utm_medium: "oa",
        landing_page: "/",
      },
    }),
  ];
}
