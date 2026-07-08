# ตั้งค่า GA4 Events เป็น Conversion (ทีละคลิก)

Property ที่ใช้: **G-MJG0VZPFKS** (Sangkan Clean)

เว็บส่ง event เหล่านี้ผ่าน `tracking.js` แล้ว:

| Event name | เมื่อไหร่ | แนะนำเป็น Conversion? |
|---|---|---|
| `click_phone` | กดลิงก์โทร | ใช่ (สำคัญ) |
| `click_line` | กดลิงก์ LINE | ใช่ (สำคัญ) |
| `click_messenger` | กด Messenger | ใช่ |
| `click_facebook` | กดลิงก์เพจ FB | ไม่จำเป็น |
| `quote_form_submit` | กดส่งฟอร์ม | ทางเลือก |
| `quote_form_success` | กลับหน้า after FormSubmit | ใช่ |
| `generate_lead` | สำเร็จฟอร์ม (มาตรฐาน GA4) | ใช่ |
| `calculator_result` | คิดราคาแล้ว | ไม่จำเป็น (engagement) |
| `hero_cta_click` | CTA ฮีโร่ | ไม่จำเป็น |
| `blog_card_click` / `blog_search` | อ่าน/ค้นบทความ | ไม่ |

> **Ads conversion** คนละเรื่อง — ต้องมี label จาก Google Ads ถึงจะยิง `conversion` ได้ (ตอนนี้ยังว่าง)

---

## A) มาร์กเป็น Key event / Conversion ใน GA4

1. เปิด [Google Analytics](https://analytics.google.com/) → เลือก property **Sangkan Clean** (`G-MJG0VZPFKS`)
2. ซ้ายล่าง **Admin (การดูแลระบบ)** → ภายใต้ Property เลือก **Events**
3. ถ้ายังไม่เห็น event ที่ต้องการ:
   - ไปหน้าเว็บ กดโทร / LINE / ส่งฟอร์มทดสอบ
   - เปิด **Reports → Realtime** ดูว่า event โผล่
   - รอ 24–48 ชม. ให้อยู่ในรายการ Events ถาวร (หรือสร้างเองในขั้น B)
4. ในหน้า **Events** หาแถว event → เปิดสวิตช์ **Mark as key event** (บาง UI เรียก Conversion)
5. ทำซ้ำสำหรับอย่างน้อย:
   - `click_phone`
   - `click_line`
   - `generate_lead` (หรือ `quote_form_success`)
   - `click_messenger` (ถ้าใช้ช่องนี้)

## B) สร้าง event เองถ้ายังไม่ขึ้นในรายการ

1. Admin → **Events** → **Create event**
2. หรือ Admin → **Key events** → **Create event** / **New key event**
3. ใส่ชื่อให้ตรงตัวอักษร เช่น `click_phone` (ตัวพิมพ์เล็กตามที่โค้ดส่ง)

## C) ตรวจว่า event ถูกยิงจริง

1. เปิดหน้าเว็บแบบไม่มี adblock
2. GA4 → **Reports → Realtime**
3. กดปุ่มโทรบนเว็บ → ควรเห็น `click_phone` ภายในไม่กี่วินาที
4. กด LINE → `click_line`
5. ส่งฟอร์มทดสอบ (หรือเปิด URL ที่มี `?submitted=true`) → `generate_lead` / `quote_form_success`

## D) (ทางเลือก) ดูใน DebugView

1. ติดตั้ง [Google Analytics Debugger](https://chrome.google.com/webstore) หรือเพิ่ม `?debug_mode=1` ตามเอกสาร GA4
2. Admin → **DebugView** → คลิก event บนเว็บ แล้วดู parameter `page_path`, `event_category`

## E) รายงานหลังตั้งค่า

- **Reports → Engagement → Events** — ปริมาณแต่ละ event
- **Advertising / Key events** (ชื่อเมนูตาม UI) — นับ conversion
- เปรียบเทียบสัปดาห์แรก: `click_line` vs `click_phone` vs `generate_lead` เพื่อดูช่องที่ลูกค้าใช้จริง

---

อัปเดตล่าสุดให้ตรงกับโค้ดใน `tracking.js` หลัง commit GA4 wiring
