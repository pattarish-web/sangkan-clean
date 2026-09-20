# Deploy Ads Attribution & Daily Lead Report

## 1. Google Ads

บัญชี `AW-18299765093` / customer `615-120-8199` (MCC `791-572-9299`)

อย่าแก้โครงแคมเปญ `SK-BigClean-Search` — Final URL ต้องเป็น `landing-bigcleaning.html`

สร้าง **Google Ads API ใหม่ใน Google Cloud** ของโปรเจ็กต์เดียวกับ OAuth ที่ใส่ Render แล้ว — อย่าสมัครโทเค็นนักพัฒนาจากศูนย์ API ของ MCC (เลิกใช้ 9 ก.ย. 2026)

1. [Google Cloud Console](https://console.cloud.google.com/) → โปรเจ็กต์ที่มี `GOOGLE_ADS_CLIENT_ID`
2. **APIs & Services → Enable APIs** → เปิด **Google Ads API**
3. เปิด [Google Ads API Overview](https://console.cloud.google.com/apis/api/googleads.googleapis.com/overview) → ถ้าขึ้น Test ให้สมัคร **Explorer** (บัญชีจริง `615-120-8199`)
4. **Credentials** → OAuth client ประเภท Desktop → Download JSON เป็น `google_ads/client_secret.json` (อย่า commit)
5. คัดลอก `google_ads/ads_api.example.env` เป็น `.env` ที่ root แล้วใส่:
   - `GOOGLE_ADS_CLIENT_ID`
   - `GOOGLE_ADS_CLIENT_SECRET`
   - `GOOGLE_ADS_REFRESH_TOKEN` (จาก `python google_ads/auth.py`)
6. **ไม่ต้องใส่** `GOOGLE_ADS_DEVELOPER_TOKEN`

จากนั้น:

```bash
pip install -r requirements.txt
python google_ads/setup_offline_conversions.py          # dry-run (ค่าเริ่มต้น)
python google_ads/setup_offline_conversions.py --apply  # เขียนบัญชีจริง
```

สคริปต์จะ:

1. เปิด **Auto-tagging** ถ้ายังปิด
2. สร้าง Offline conversions ชนิด `UPLOAD_CLICKS` ชื่อ `phone_click`, `line_click`, `qualified_lead` และ `won_deal` (ค่าเป็น THB สำหรับ won)
3. ตั้ง **เป้าหมายโฆษณาหลัก** เป็น `phone_click` + `line_click` + ฟอร์ม `generate_lead`
4. ตั้ง `qualified_lead` / `won_deal` เป็น observe-only (`primary_for_goal=false`)
5. ตั้ง conversion เว็บไซต์โทร/LINE เดิม และ GA4-imported `click_phone` / `click_line` ให้ไม่เป็นเป้าหมายโฆษณา
6. **ไม่** เปลี่ยน Final URL ของแคมเปญ — ValueTrack เป็นทางเลือก: `{lpurl}?campaignid={campaignid}&adgroupid={adgroupid}&creative={creative}&keyword={keyword}` (`gclid` มาจาก auto-tagging)

ยืนยันลีดแล้วระบบยิง Google Ads API (`uploadClickConversions`) ทันที — CSV เป็นไฟล์สำรองของแถวที่ยังไม่ส่งสำเร็จเท่านั้น

## 2. Render (ops webhook)

เพิ่ม env:

| Key | หมายเหตุ |
|-----|----------|
| `LEAD_STAFF_TOKEN` | รหัสเข้า `/ops/leads` — ยาวและสุ่ม |
| `LEAD_ALLOWED_ORIGINS` | `https://www.sangkanclean.com,https://sangkanclean.com` |
| `LEAD_SEED_DEMO` | ต้องเป็น `0` หรือไม่ตั้ง บนโปรดักชัน |
| `TRUST_PROXY` | `1` บน Render |
| `LEAD_API_PUBLIC_URL` | ยังไม่ต้องใส่ที่นี่ — ใส่ฝั่งเว็บ |
| `GOOGLE_SHEETS_ID` | สเปรดชีตลีด (แท็บใหม่แยกจาก LINE) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSON ของ service account — ระบบจะใช้ Sheets เป็นที่เก็บหลัก |
| `LEAD_STORE_FILE` | **อย่าตั้ง** บนโปรดักชัน ถ้าอยากใช้ Sheets (ตั้งแล้วจะบังคับไฟล์ท้องถิ่น) |
| `GOOGLE_ADS_CLIENT_ID` | OAuth จาก Cloud โปรเจ็กต์ที่เปิด Google Ads API |
| `GOOGLE_ADS_CLIENT_SECRET` | OAuth |
| `GOOGLE_ADS_REFRESH_TOKEN` | จาก `python google_ads/auth.py` |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | ไม่ต้องใส่ (เลิกใช้ 9 ก.ย. 2026) |

แท็บ Google Sheets ใหม่ (แยกจาก `customers` ของ LINE):

`leads`, `lead_pipeline`, `lead_attribution`, `lead_dashboard`, `ads_conversions`

รัน `node ops/webhook/scripts/setup-lead-tabs.mjs` หลังมี service account

ถ้าไม่มี Sheets credentials ระบบจะถอยไปไฟล์ `ops/webhook/data/leads.json` ซึ่งบน Render จะหายเมื่อเครื่องรีสตาร์ท — อย่าใช้โหมดนี้บนโปรดักชัน

## 3. เว็บไซต์ (GitHub Pages)

ตั้ง secret/ตัวแปร:

- `LEAD_API_PUBLIC_URL=https://<render-host>/api/leads`
- `ADS_LEAD_CONVERSION_LABEL=<label ของ generate_lead เว็บไซต์>` (หรือนำเข้า GA4 `generate_lead` แทน)

แล้วรัน `python build_assets.py` หรือใส่ใน `window.LEAD_API_URL` ก่อน `lead-form.js`

ถ้ายังไม่ตั้ง `LEAD_API_PUBLIC_URL` ฟอร์มจะส่ง FormSubmit เหมือนเดิม — เว็บไม่พัง

`window.adsLeadSendTo` ชี้เฉพาะ conversion ฟอร์ม ไม่ fallback ไปโทร/LINE

## 4. ใช้ประจำหลังเปิดแคมเปญ

กดยืนยันใน `/ops/leads` แล้วยิง Google Ads API (`uploadClickConversions`) ทันที — ไม่ต้องอิมพอร์ต CSV ทุกวัน

ต้องมี `GOOGLE_ADS_*` บน Render และต้องรัน `setup_offline_conversions.py --apply` ให้มี conversion ชื่อ `phone_click`, `line_click`, `qualified_lead`, `won_deal` ก่อน

ถ้ายิงไม่สำเร็จ แถวยังอยู่ในคิว `pending`/`failed`:

- กด **ส่งคิวเข้า Google Ads** ใน Dashboard
- หรือรัน GitHub Action `ads-upload-conversions` แบบมือ (workflow_dispatch) จะ `POST {LEAD_API_PUBLIC_URL}/ads-conversions/upload`
- CSV ดาวน์โหลดได้เป็นทางสำรองของแถวที่ยังไม่ส่งสำเร็จ

ตั้ง GitHub secrets: `LEAD_API_PUBLIC_URL=https://<render-host>/api/leads` และ `LEAD_STAFF_TOKEN` (ค่าเดียวกับ Render) — **อย่า** ใส่ Ads OAuth ใน GitHub Actions

## 5. Looker Studio (ทางเลือก)

เชื่อมแท็บ `lead_dashboard` + Google Ads + GA4  
ห้ามดึงคอลัมน์ชื่อ/เบอร์โทรไปแสดงในรายงานที่แชร์กว้าง

## 6. ตรวจก่อนปล่อย

- [ ] คลิกลิงก์ Ads แล้ว `gclid` ยังอยู่บนหน้าแลนดิง
- [ ] ส่งฟอร์มแล้วมีแถวในรายงานกิจกรรม และยิง `generate_lead` **ครั้งเดียว**
- [ ] กดโทรและ LINE แล้วมีแถวสถานะ “คลิก—รอตรวจสอบ” พร้อมเวลาและ attribution — **ยังไม่** ขึ้น conversion ใน Google Ads
- [ ] กรอกชื่อ เบอร์ แล้วกดยืนยันใน Dashboard จึงยิง `phone_click` / `line_click` เข้า Google Ads API
- [ ] ปิด API ชั่วคราว แล้วยังได้เมล FormSubmit
- [ ] กดโทร/LINE แล้วยังโทรออก/เปิด LINE ได้ และยังบันทึกลงรายงาน
- [ ] ไฟล์ CSV ไม่มีชื่อหรือเบอร์โทร และมีเฉพาะแถวที่ยังไม่ส่งสำเร็จ
- [ ] `/ops/leads` เข้าไม่ได้ถ้าไม่มีโทเคน
- [ ] Render ใช้ Sheets (ไม่ตั้ง `LEAD_STORE_FILE`, `LEAD_SEED_DEMO` ไม่เป็น `1`)
