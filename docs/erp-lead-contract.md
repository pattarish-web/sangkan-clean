# Lead contract for Sangkan Clean ERP

Marketing site (`pattarish-web/sangkan-clean`) owns capture. ERP owns quotations, tax documents, and the customer master. Do not duplicate a CRM in this repo.

## Event: `lead.created`

```json
{
  "id": "LD-20260919-AB12",
  "created_at": "2026-09-19T10:12:00+07:00",
  "name": "string",
  "phone": "0XXXXXXXXX",
  "service": "Big Cleaning|Sangkan Office|แม่บ้านประจำ|ทำความสะอาดทั่วไป|หลังก่อสร้าง|อื่นๆ",
  "area": "string",
  "message": "string",
  "consent": true,
  "page_path": "/",
  "attribution": {
    "channel": "google_ads|facebook|line|organic|direct|referral",
    "gclid": "string|empty",
    "utm_source": "string",
    "utm_campaign": "string",
    "keyword": "string",
    "first_channel": "string",
    "landing_page": "/landing-bigcleaning.html"
  }
}
```

## Event: `deal.updated`

```json
{
  "lead_id": "LD-20260919-AB12",
  "status": "unverified|new|contacted|qualified|quoted|won|lost",
  "value_thb": 18500,
  "lost_reason": "string",
  "updated_at": "2026-09-19T16:00:00+07:00"
}
```

ERP may store `lead_id` on a Deal. Sync is one-way until the ERP spine is ready: website/Sheets → ERP, never the reverse for marketing attribution fields.
