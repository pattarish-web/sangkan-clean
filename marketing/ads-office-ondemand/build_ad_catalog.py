"""Rebuild catalog with diverse art variants per venue (less background reuse)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "genz" / "batch"

SERVICES = [
    {"id": "bigclean", "name": "Big Cleaning", "price": "เริ่ม ฿5,500", "hook": "ขจัดคราบฝังลึก"},
    {"id": "maid", "name": "แม่บ้านประจำ", "price": "เริ่ม ฿12,000/เดือน", "hook": "มีคนสำรองทดแทน"},
    {"id": "office", "name": "แม่บ้านออฟฟิศ On-Demand", "price": "เริ่ม ฿2,900/เดือน", "hook": "ไม่ต้องจ้างประจำ"},
    {"id": "soft", "name": "Soft Cleaning", "price": "เริ่ม ฿3,500", "hook": "อ่อนโยนกับพื้นผิว"},
    {"id": "glass", "name": "เช็ดกระจกอาคารสูง", "price": "สอบถามราคา", "hook": "มาตรฐานความปลอดภัย"},
    {"id": "carpet", "name": "ซักพรม โซฟา ผ้าม่าน", "price": "เริ่ม ฿800", "hook": "ขจัดคราบ ไรฝุ่น"},
    {"id": "ozone", "name": "อบโอโซน", "price": "เริ่ม ฿1,200", "hook": "ฆ่าเชื้อ กำจัดกลิ่น"},
]

# 3 art variants each → 12 venues × 3 = 36 unique backgrounds
VENUES = [
    {"id": "office", "th": "ออฟฟิศ", "arts": ["art-office", "art-office-v2", "art-office-v3"]},
    {"id": "factory", "th": "โรงงาน", "arts": ["art-factory", "art-factory-v2", "art-factory-v3"]},
    {"id": "warehouse", "th": "โกดัง", "arts": ["art-warehouse", "art-warehouse-v2", "art-warehouse-v3"]},
    {"id": "hotel", "th": "โรงแรม", "arts": ["art-hotel", "art-hotel-v2", "art-hotel-v3"]},
    {"id": "hospital", "th": "โรงพยาบาล", "arts": ["art-hospital", "art-hospital-v2", "art-hospital-v3"]},
    {"id": "school", "th": "โรงเรียน", "arts": ["art-school", "art-school-v2", "art-school-v3"]},
    {"id": "mall", "th": "ห้างสรรพสินค้า", "arts": ["art-mall", "art-mall-v2", "art-mall-v3"]},
    {"id": "cafe", "th": "คาเฟ่", "arts": ["art-cafe", "art-cafe-v2", "art-cafe-v3"]},
    {"id": "showroom", "th": "โชว์รูม", "arts": ["art-showroom", "art-showroom-v2", "art-showroom-v3"]},
    {"id": "highrise", "th": "ตึกสูง", "arts": ["art-highrise", "art-highrise-v2", "art-highrise-v3"]},
    {"id": "gym", "th": "ฟิตเนส", "arts": ["art-gym", "art-gym-v2", "art-gym-v3"]},
    {"id": "condo", "th": "คอนโด", "arts": ["art-condo", "art-condo-v2", "art-condo-v3"]},
]

ANGLES = [
    {"id": "hook", "chip": "ทีมมืออาชีพ", "cta": "ทัก LINE @sangkanclean"},
    {"id": "speed", "chip": "เข้างานไว", "cta": "โทร 092-914-9978 / 080-694-1998"},
    {"id": "trust", "chip": "รับประกันคุณภาพ", "cta": "ขอใบเสนอราคา"},
]

EXTRAS = [
    {"headline": ["Big Cleaning", "ขจัดคราบฝังลึก"], "sub": "โรงงาน อาคาร สำนักงาน · เริ่ม ฿5,500", "chip": "Deep Clean", "arts": ["art-factory-v2", "art-factory-v3"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["แม่บ้านประจำ", "มีคนสำรอง"], "sub": "สำนักงาน คอนโด อาคาร · เริ่ม ฿12,000/เดือน", "chip": "Spare Ready", "arts": ["art-office-v2", "art-condo-v2"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["เลิกจ้างประจำ", "ได้แล้ว"], "sub": "แม่บ้านออฟฟิศ On-Demand · อุดมสุข เริ่ม ฿2,900", "chip": "สำหรับทีมวัยใหม่", "arts": ["art-office-v3", "art-office"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["เช็คอิน GPS", "ส่งรูปก่อน–หลัง"], "sub": "โปร่งใส มองเห็นงานจริง · Sangkan Office", "chip": "Tech-Enabled", "arts": ["art-office-v2", "art-highrise-v2"], "cta": "ดูแพ็ค S / M"},
    {"headline": ["ชวนเพื่อนในโซน", "เครดิตคืน 10%"], "sub": "สะสมถึงสิ้นปี · ใช้จนกว่าจะหมด", "chip": "Affiliate", "arts": ["art-cafe-v2", "art-mall-v2"], "cta": "ขอโค้ดที่ LINE"},
    {"headline": ["จองก่อน", "เริ่มเดือนหน้า"], "sub": "Early Bird · อุดมสุข–บางนา", "chip": "EARLY BIRD", "arts": ["art-condo-v3", "art-office-v3"], "cta": "ทัก LINE จองเลย"},
    {"headline": ["อบโอโซน", "ฆ่าเชื้อ กำจัดกลิ่น"], "sub": "มาตรฐานปลอดภัย · เริ่ม ฿1,200", "chip": "Hygiene", "arts": ["art-hospital-v2", "art-hospital-v3"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["ซักพรม โซฟา", "ขจัดไรฝุ่น"], "sub": "เริ่มต้น ฿800 · ทีมมืออาชีพ", "chip": "Deep Fabric", "arts": ["art-hotel-v2", "art-condo-v2"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["เช็ดกระจก", "อาคารสูง"], "sub": "อุปกรณ์มาตรฐานความปลอดภัย", "chip": "Safety First", "arts": ["art-highrise-v2", "art-highrise-v3"], "cta": "สอบถามราคา"},
    {"headline": ["30+ ปี", "ประสบการณ์"], "sub": "5,000+ โปรเจกต์ · รับประกันคุณภาพ 100%", "chip": "Trusted", "arts": ["art-hotel-v3", "art-showroom-v2"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["เข้างานภายใน", "24 ชม."], "sub": "รับงานด่วน · กรุงเทพและปริมณฑล", "chip": "Speed", "arts": ["art-warehouse-v2", "art-factory-v2"], "cta": "โทร 092-914-9978 / 080-694-1998"},
    {"headline": ["มาตรฐานเคมี", "ISO / อย."], "sub": "SevenSave · ปลอดภัยต่อคนและสิ่งแวดล้อม", "chip": "Green", "arts": ["art-hospital", "art-school-v2"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["Soft Cleaning", "ดูแลประจำ"], "sub": "อ่อนโยนกับพื้นผิว · เริ่ม ฿3,500", "chip": "Gentle Care", "arts": ["art-showroom-v3", "art-cafe-v3"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["ครอบคลุม", "กทม. + ปริมณฑล"], "sub": "บางนา อุดมสุข ระยอง ชลบุรี และทั่วประเทศ", "chip": "Service Area", "arts": ["art-mall-v3", "art-highrise"], "cta": "ทัก LINE @sangkanclean"},
    {"headline": ["มีประกัน", "ความเสียหาย"], "sub": "ทำงานในนามบริษัท · มั่นใจได้", "chip": "100% Trust", "arts": ["art-office", "art-gym-v2"], "cta": "ขอใบเสนอราคา"},
    {"headline": ["คำนวณราคา", "ฟรีทันที"], "sub": "โปร่งใส ไม่มีค่าแอบแฝง · sangkanclean.com", "chip": "Transparent", "arts": ["art-gym-v3", "art-school-v3"], "cta": "ทัก LINE @sangkanclean"},
]


def build() -> list[dict]:
    items: list[dict] = []
    n = 0
    for venue in VENUES:
        for si, svc in enumerate(SERVICES):
            n += 1
            angle = ANGLES[(n - 1) % len(ANGLES)]
            art = venue["arts"][si % len(venue["arts"])]
            items.append(
                {
                    "id": f"{n:03d}-{svc['id']}-{venue['id']}-{angle['id']}",
                    "chip": angle["chip"],
                    "headline": [svc["name"], f"สำหรับ{venue['th']}"],
                    "sub": f"{svc['hook']} · {svc['price']}",
                    "cta": angle["cta"],
                    "art": art,
                    "service": svc["id"],
                    "venue": venue["id"],
                }
            )

    for ei, extra in enumerate(EXTRAS):
        n += 1
        art = extra["arts"][ei % len(extra["arts"])]
        items.append(
            {
                "id": f"{n:03d}-extra-{extra['chip'].lower().replace(' ', '-').replace('/', '-')}",
                "chip": extra["chip"],
                "headline": extra["headline"],
                "sub": extra["sub"],
                "cta": extra["cta"],
                "art": art,
                "service": "site",
                "venue": "mix",
            }
        )
    return items[:100]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    items = build()
    path = OUT / "catalog.json"
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    arts = sorted({i["art"] for i in items})
    print(f"wrote {path} ({len(items)} creatives)")
    print(f"unique backgrounds: {len(arts)}")
    print(", ".join(arts))


if __name__ == "__main__":
    main()
