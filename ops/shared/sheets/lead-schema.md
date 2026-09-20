# Marketing Lead Sheets (แยกจาก LINE Office)

อย่าใส่ลีดเว็บลงแท็บ `customers` ของ Sangkan Office

Spreadsheet เดิมหรือไฟล์ใหม่ก็ได้ แต่ต้องมี 5 แท็บนี้:

## leads

id, created_at, created_date_bkk, event_type, contact_method, clicked_target, name, phone, service, area, message, consent, status, value_thb, lost_reason, note, page_path, idempotency_key, gclid, channel, first_channel, utm_source, utm_campaign, keyword, landing_page, ads_contact_sent_at, ads_qualified_sent_at, ads_won_sent_at, ads_order_id

- `event_type`: `form_submit`, `phone_click` หรือ `line_click`
- คลิกโทร/LINE เริ่มที่ `status=unverified` และยังไม่มีชื่อ/เบอร์ลูกค้า
- ผู้ดูแลเทียบ `created_at` (เวลาไทยใน Dashboard) กับประวัติสายหรือ LINE แล้วกรอกข้อมูลและเปลี่ยนสถานะอย่างน้อยเป็น `contacted`
- หลังยืนยันแล้วระบบยิง Google Ads API ทันที และคิว `phone_click` / `line_click` เข้า `ads_conversions` (เฉพาะเมื่อมี GCLID) — คลิกดิบไม่ถูกส่งไป Google Ads
- มาร์ก `lost` จากสถานะรอตรวจสอบ = ไม่ใช่ลูกค้าจริง และไม่ส่ง Ads
- ฟอร์มเป็น `contact_method=form` / `event_type=form_submit` สถานะเริ่มที่ `new` — Ads เว็บไซต์ยิง `generate_lead` ครั้งเดียว ไม่คิว `phone_click`/`line_click`

## lead_pipeline

lead_id, status, value_thb, lost_reason, updated_at, updated_by

## lead_attribution

lead_id, gclid, gbraid, wbraid, utm_source, utm_medium, utm_campaign, utm_content, utm_term, campaignid, adgroupid, creative, keyword, first_channel, last_channel, landing_page, referrer

## lead_dashboard

date_bkk, leads, qualified, won, revenue_thb, google_ads, facebook, line, organic, other

## ads_conversions

gclid, conversion_name, conversion_time, conversion_value, conversion_currency, order_id, upload_status, uploaded_at, upload_error

`ads_conversions` เป็นชุดที่อนุญาตให้ส่งเข้า Google Ads ได้เพียงชุดนี้ — ห้ามมี name/phone/email/message

`upload_status`: `pending` → `uploaded` หรือ `failed` (กดส่งซ้ำได้จาก Dashboard)
