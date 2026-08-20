"""
Smart Offline GEO upgrade — no Gemini API.

Builds GEO HTML (Key Takeaways / เนื้อหาหลัก / สถิติ / FAQ) from
service type + place type parsed from each post title.
Skips posts already marked geo_source=gemini or that already have
GEO content from Gemini (agentwork will set geo_source).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from typing import Any

from build_blogs import slugify

GEO_MARKER = "สรุปประเด็นสำคัญ"


PLACE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("condo", ("คอนโด",)),
    ("showroom", ("โชว์รูม",)),
    ("clinic", ("คลินิก",)),
    ("fitness", ("ฟิตเนส", "ฟิตเนส")),
    ("cafe", ("คาเฟ่", "ร้านกาแฟ")),
    ("office", ("ออฟฟิศ", "สำนักงาน")),
    ("factory", ("โรงงาน",)),
    ("hospital", ("โรงพยาบาล",)),
    ("hotel", ("โรงแรม",)),
    ("resort", ("รีสอร์ท", "รีสอร์ต")),
    ("school", ("โรงเรียน",)),
    ("university", ("มหาวิทยาลัย",)),
    ("mall", ("ห้างสรรพสินค้า", "ศูนย์การค้า", "ห้าง")),
    ("restaurant", ("ร้านอาหาร",)),
    ("warehouse", ("โกดัง",)),
    ("building", ("ตึกสูง", "อาคารพานิชย์", "อาคาร")),
    ("home", ("บ้าน",)),
]

SERVICE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("big_cleaning", ("บิ๊กคลีนนิ่ง", "big cleaning", "bigcleaning", "หลังก่อสร้าง")),
    ("maid", ("แม่บ้าน", "หาแม่บ้าน")),
    ("contract", ("รับเหมา", "จ้างทำความสะอาด", "รับทำความสะอาด")),
    ("clear_area", ("เคลียร์พื้นที่", "เคลียร์")),
    ("find_cleaner", ("หาคนทำความสะอาด",)),
]


PLACE_COPY: dict[str, dict[str, Any]] = {
    "condo": {
        "label": "คอนโดมิเนียม",
        "pain": "พื้นที่ส่วนกลาง ลิฟต์ ระเบียง และคราบในห้องน้ำที่สะสมเร็ว",
        "focus": "ทำความสะอาดห้องชุด พื้นที่ส่วนกลาง และจุดเสี่ยงเชื้อโรคโดยไม่รบกวนลูกบ้าน",
        "stat": "พื้นที่อยู่อาศัยแนวสูงจำนวนมากในเมืองใหญ่มีการหมุนเวียนการใช้พื้นที่ส่วนกลางสูง ทำให้ฝุ่นและคราบสะสมเร็วขึ้น",
    },
    "showroom": {
        "label": "โชว์รูม",
        "pain": "ฝุ่นบนพื้นผิวสินค้า รอยนิ้วมือบนกระจก และภาพลักษณ์แบรนด์ตอนลูกค้าเข้าชม",
        "focus": "รักษาพื้นผิวโชว์สินค้า กระจก และพื้นที่เดินให้เงางามพร้อมรับลูกค้า",
        "stat": "หน้าสัมผัสสินค้าและกระจกโชว์เป็นจุดที่ลูกค้าจดจำภาพลักษณ์แบรนด์ได้เร็วที่สุด",
    },
    "clinic": {
        "label": "คลินิก",
        "pain": "ความเสี่ยงเชื้อโรคในจุดสัมผัส พื้นที่รอ และห้องตรวจ",
        "focus": "ฆ่าเชื้อจุดสัมผัสบ่อย ทำความสะอาดพื้นผิวทางการแพทย์รองรับ และกลิ่นอับ",
        "stat": "สถานพยาบาลขนาดเล็กมีการสัมผัสพื้นผิวซ้ำสูง จึงต้องเน้นสุขอนามัยมากกว่าความสะอาดผิวเผิน",
    },
    "fitness": {
        "label": "ฟิตเนส",
        "pain": "เหงื่อ กลิ่น และแบคทีเรียบนเครื่องออกกำลังกาย",
        "focus": "ฆ่าเชื้อเครื่องเล่น พื้นยาง และจุดสัมผัสที่ใช้ร่วมกัน",
        "stat": "พื้นที่ออกกำลังกายมีอัตราการใช้ซ้ำของอุปกรณ์สูง ทำให้ต้องทำความสะอาดบ่อยเป็นพิเศษ",
    },
    "cafe": {
        "label": "คาเฟ่",
        "pain": "คราบเครื่องดื่ม กลิ่นอาหาร และพื้นหลังเคาน์เตอร์",
        "focus": "ดูแลโซนลูกค้า โซนครัวเบา และสุขอนามัยที่มองเห็นได้ชัด",
        "stat": "ธุรกิจอาหารเครื่องดื่มได้รับผลจากภาพลักษณ์ความสะอาดทันทีที่มีลูกค้านั่งทาน",
    },
    "office": {
        "label": "ออฟฟิศ/สำนักงาน",
        "pain": "ฝุ่นโต๊ะทำงาน พื้นที่ประชุม และห้องน้ำพนักงาน",
        "focus": "รักษาพื้นที่ทำงานให้สะอาดต่อเนื่อง ลดป่วยจากการสะสมฝุ่น",
        "stat": "สำนักงานจำนวนมากพบว่าความสะอาดสัมพันธ์กับความพึงพอใจของพนักงานอย่างมีนัย",
    },
    "factory": {
        "label": "โรงงาน",
        "pain": "ฝุ่นอุตสาหกรรม คราบน้ำมัน และความปลอดภัยบนพื้นทางเดิน",
        "focus": "ทำความสะอาดเชิงอุตสาหกรรม เน้นความปลอดภัยและมาตรฐานพื้นที่ผลิต",
        "stat": "พื้นที่ผลิตที่สะอาดช่วยลดอุบัติเหตุลื่นล้มและรักษาคุณภาพงานได้ดีขึ้น",
    },
    "hospital": {
        "label": "โรงพยาบาล",
        "pain": "เชื้อโรคในจุดสัมผัส พื้นที่รอคนไข้ และห้องน้ำสาธารณะ",
        "focus": "ทำความสะอาดพร้อมแนวทางสุขอนามัยสูงสำหรับสถานพยาบาล",
        "stat": "สถานพยาบาลต้องการรอบทำความสะอาดที่บ่อยและมาตรฐานสูงกว่าอาคารทั่วไป",
    },
    "hotel": {
        "label": "โรงแรม",
        "pain": "ห้องพักหมุนเวียนเร็ว พื้นที่ล็อบบี้ และห้องน้ำแขก",
        "focus": "รักษามาตรฐานบริการที่แขกสัมผัสได้ทันทีตั้งแต่เช็คอิน",
        "stat": "รีวิวที่พักมักอ้างถึงความสะอาดเป็นปัจจัยตัดสินใจหลักของผู้เข้าพัก",
    },
    "resort": {
        "label": "รีสอร์ท",
        "pain": "พื้นที่เปิด ชื้น และห้องพักที่ต้องการความสดชื่น",
        "focus": "ดูแลห้องพักและพื้นที่ส่วนกลางให้พร้อมต้อนรับแขก",
        "stat": "ที่พักแนวรีสอร์ทต้องรับมือความชื้นและฝุ่นจากพื้นที่เปิดโล่งมากกว่าโรงแรมในเมือง",
    },
    "school": {
        "label": "โรงเรียน",
        "pain": "ฝุ่นห้องเรียน ห้องน้ำนักเรียน และพื้นที่สนาม",
        "focus": "สุขอนามัยสำหรับเด็กและบุคลากรในอาคารเรียน",
        "stat": "สถานศึกษาที่มีการใช้พื้นที่หนาแน่นต้องจัดรอบทำความสะอาดชัดเจนเพื่อลดการสะสมเชื้อ",
    },
    "university": {
        "label": "มหาวิทยาลัย",
        "pain": "อาคารเรียนขนาดใหญ่ ห้องแล็บ และพื้นที่ไม่ว่าง",
        "focus": "จัดแผนทำความสะอาดตามโซนและช่วงเวลาเรียน",
        "stat": "อาคารขนาดใหญ่มีการสัญจรสูง จึงต้องแบ่งโซนทำความสะอาดให้ครอบคลุม",
    },
    "mall": {
        "label": "ศูนย์การค้า/ห้าง",
        "pain": "คนเดินหนาแน่น ห้องน้ำสาธารณะ และคราบบนพื้นทางเดิน",
        "focus": "ทำความสะอาดต่อเนื่องระหว่างเปิดร้านและปิดห้าง",
        "stat": "พื้นที่ค้าปลีกขนาดใหญ่มีปริมาณผู้ใช้งานต่อวันสูงมากเมื่อเทียบกับอาคารทั่วไป",
    },
    "restaurant": {
        "label": "ร้านอาหาร",
        "pain": "คราบน้ำมัน กลิ่น และสุขอนามัยครัว/โซนลูกค้า",
        "focus": "ทำความสะอาดครัวเบา-หนัก และพื้นที่นั่งทานอย่างเป็นระบบ",
        "stat": "ร้านอาหารถูกตรวจสอบด้วยตาและความคาดหวังด้านสุขอนามัยจากลูกค้าสูงเป็นพิเศษ",
    },
    "warehouse": {
        "label": "โกดัง",
        "pain": "ฝุ่นชั้นวาง สิ่งตกค้าง และพื้นทางขนส่ง",
        "focus": "เคลียร์ฝุ่น ทางเดิน และพื้นที่จัดเก็บให้ใช้งานปลอดภัย",
        "stat": "โกดังที่มีฝุ่นสูงมักกระทบทั้งสุขภาพพนักงานและความเรียบร้อยของสินค้าคงคลัง",
    },
    "building": {
        "label": "อาคาร/ตึกสูง",
        "pain": "พื้นที่ส่วนกลางหลายชั้น ลิฟต์ และห้องน้ำรอบอาคาร",
        "focus": "วางแผนทำความสะอาดตามชั้นและจุดใช้งานหนาแน่น",
        "stat": "อาคารสูงมีจุดสัมผัสร่วมจำนวนมาก จึงต้องหมุนเวียนทีมให้ครอบคลุมทั้งอาคาร",
    },
    "home": {
        "label": "บ้านพักอาศัย",
        "pain": "ฝุ่นในบ้าน ห้องน้ำ ครัว และมุมอับ",
        "focus": "ทำความสะอาด घरครบวงจร เน้นพื้นที่ใช้ชีวิตประจำวัน",
        "stat": "บ้านที่มีกิจกรรมสูงจะสะสมฝุ่นและคราบเร็ว โดยเฉพาะครัวและห้องน้ำ",
    },
    "generic": {
        "label": "พื้นที่ใช้งาน",
        "pain": "ฝุ่น คราบฝังลึก และจุดสัมผัสที่ใช้ร่วมกัน",
        "focus": "ทำความสะอาดเชิงลึกอย่างเป็นระบบตามลักษณะพื้นที่",
        "stat": "ธุรกิจและที่อยู่อาศัยจำนวนมากพบว่าการทำความสะอาดมืออาชีพช่วยลดเวลาและผลลัพธ์ไม่แน่นอน",
    },
}


SERVICE_COPY: dict[str, dict[str, Any]] = {
    "big_cleaning": {
        "label": "Big Cleaning",
        "takeaways": [
            "เหมาะกับงานทำความสะอาดเชิงลึกเป็นรอบใหญ่ หรือก่อนเปิดใช้งานพื้นที่",
            "ครอบคลุมคราบฝังลึก จุดอับ และพื้นผิวที่ทำความสะอาดทั่วไปเข้าไม่ถึง",
            "ช่วยรีเซ็ตมาตรฐานความสะอาดของพื้นที่ให้พร้อมใช้งานระยะยาว",
        ],
        "method": "ทีมจะประเมินพื้นที่ แบ่งโซนงาน แล้วลงมือทำความสะอาดเชิงลึกตามระดับความสกปรก พร้อมตรวจ QC ก่อนส่งมอบ",
    },
    "maid": {
        "label": "แม่บ้านประจำ/แม่บ้านตามไซต์",
        "takeaways": [
            "เหมาะกับพื้นที่ที่ต้องการความสะอาดต่อเนื่องเป็นประจำ",
            "วางแผนรอบงานได้ตามความถี่ของพื้นที่ (รายวัน/รายสัปดาห์)",
            "ลดภาระเจ้าของพื้นที่และรักษาภาพลักษณ์สม่ำเสมอ",
        ],
        "method": "ทีมแม่บ้านทำงานตามเช็คลิสต์ประจำจุด ครอบคลุมพื้นผิวหลัก จุดสัมผัส และห้องน้ำ พร้อมรายงานความเรียบร้อย",
    },
    "contract": {
        "label": "รับเหมาทำความสะอาด",
        "takeaways": [
            "เหมาะกับองค์กรที่ต้องการผู้รับเหมาชัดเจนขอบเขตงานและรอบบริการ",
            "วางแผนทีม อุปกรณ์ และมาตรฐานงานให้สอดคล้องกับประเภทพื้นที่",
            "มีหัวหน้างานคุมคุณภาพเพื่อลดงานแก้ซ้ำ",
        ],
        "method": "เริ่มจากสำรวจพื้นที่ กำหนดขอบเขตและรอบงาน จากนั้นจัดทีมเข้าปฏิบัติการตามแผนที่ตกลงกันไว้",
    },
    "clear_area": {
        "label": "เคลียร์พื้นที่",
        "takeaways": [
            "เหมาะกับงานเคลียร์ของที่ไม่ใช้ ขยะตกแต่ง หรือพื้นที่หลังกิจกรรม",
            "ช่วยให้อาคารพร้อมตกแต่งใหม่หรือเปิดใช้งานได้เร็วขึ้น",
            "เน้นคัดแยก ขนย้าย และทำความสะอาดต่อเนื่องหลังเคลียร์",
        ],
        "method": "ทีมจะคัดแยกสิ่งของ เคลียร์ขยะ/วัสดุ และเก็บงานพื้นผิวให้พื้นที่กลับมามีระเบียบพร้อมใช้",
    },
    "find_cleaner": {
        "label": "จัดหาทีมทำความสะอาด",
        "takeaways": [
            "ช่วยจับคู่ทีมมืออาชีพกับประเภทงานและความถี่ที่ต้องการ",
            "ลดความเสี่ยงจ้างทีมไม่ตรงสเปกพื้นที่",
            "ได้มาตรฐานงานจากแบรนด์ที่มีกระบวนการชัดเจน",
        ],
        "method": "ประเมินความต้องการ จากนั้นจัดทีมตามลักษณะงาน อุปกรณ์ และตารางที่เหมาะสมกับไซต์",
    },
    "generic": {
        "label": "บริการทำความสะอาดมืออาชีพ",
        "takeaways": [
            "ทีมงานผ่านการอบรมและใช้อุปกรณ์ที่เหมาะกับพื้นผิวแต่ละประเภท",
            "เน้นผลลัพธ์ที่ตรวจวัดได้ ไม่ใช่แค่ปัดกวาดผิวเผิน",
            "วางแผนงานให้กระทบการใช้งานพื้นที่ให้น้อยที่สุด",
        ],
        "method": "ประเมินพื้นที่ เลือกวิธีและน้ำยาที่เหมาะสม แล้วทำความสะอาดตามขั้นตอนพร้อมตรวจสอบก่อนส่งมอบ",
    },
}


FAQ_BANK = [
    (
        "ต้องเตรียมอุปกรณ์เองหรือไม่?",
        "ไม่ต้องครับ ทีมงาน Sangkan Clean เตรียมอุปกรณ์และน้ำยาที่เหมาะกับประเภทงานไปให้ครบ",
    ),
    (
        "ใช้เวลานานแค่ไหน?",
        "ขึ้นกับขนาดพื้นที่และความสกปรกครับ ทีมจะประเมินและแจ้งกรอบเวลาก่อนเริ่มงาน",
    ),
    (
        "น้ำยาปลอดภัยต่อเด็กและสัตว์เลี้ยงไหม?",
        "เราคัดน้ำยาที่เหมาะกับการใช้งานจริง และแจ้งข้อควรระวังตามประเภทพื้นผิวก่อนเริ่มงาน",
    ),
    (
        "รับประกันงานอย่างไร?",
        "หากพบจุดที่ไม่เรียบร้อยหลังส่งมอบในเงื่อนไขที่ตกลง ทีมยินดีกลับไปปรับแก้ให้",
    ),
    (
        "สามารถนัดล่วงหน้าหรือเข้างานนอกเวลาได้ไหม?",
        "ได้ครับ แจ้งช่วงเวลาที่สะดวกมาได้ ทีมจะจัดตารางให้กระทบการใช้งานน้อยที่สุด",
    ),
]


def _seed_rng(seed_text: str):
    import random

    digest = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    rng = random.Random(int(digest[:16], 16))
    return rng


def extract_keyword(title: str) -> str:
    text = title.strip()
    text = re.sub(r"^บริการ\s*", "", text)
    text = re.sub(r"\s*ระดับมืออาชีพ.*$", "", text)
    text = re.sub(r"\s*[–-]\s*Sangkan Clean.*$", "", text, flags=re.IGNORECASE)
    return text.strip() or title.strip()


def detect_place(text: str) -> str:
    lower = text.lower()
    for place_id, words in PLACE_KEYWORDS:
        for w in words:
            if w.lower() in lower:
                return place_id
    return "generic"


def detect_service(text: str) -> str:
    lower = text.lower()
    for service_id, words in SERVICE_KEYWORDS:
        for w in words:
            if w.lower() in lower:
                return service_id
    if "ทำความสะอาด" in text:
        return "contract"
    return "generic"


def is_gemini_post(post: dict) -> bool:
    return post.get("geo_source") == "gemini"


def needs_offline_upgrade(post: dict) -> bool:
    if is_gemini_post(post):
        return False
    # Re-run offline only when not yet marked offline and not gemini.
    # Posts with GEO marker but no source were likely from earlier Gemini runs — preserve them as gemini.
    content = post.get("content", "")
    if GEO_MARKER in content and post.get("geo_source") not in ("offline", "gemini"):
        return False
    if post.get("geo_source") == "offline" and GEO_MARKER in content:
        return False
    return GEO_MARKER not in content


def build_geo_html(title: str, description: str, slug: str = "") -> str:
    keyword = extract_keyword(title)
    service_id = detect_service(title)
    place_id = detect_place(title)
    service = SERVICE_COPY[service_id]
    place = PLACE_COPY[place_id]
    rng = _seed_rng(slug or keyword)

    takeaways = list(service["takeaways"])
    takeaways.append(
        f"เหมาะกับ{place['label']} ที่ต้องการ{place['focus']}"
    )
    takeaways = takeaways[:4]

    faq_items = rng.sample(FAQ_BANK, 3)
    faq_items[0] = (
        f"{service['label']} สำหรับ{place['label']} ต่างจากงานทั่วไปอย่างไร?",
        f"งาน{keyword} จะโฟกัส{place['focus']} เป็นพิเศษ พร้อมเลือกวิธีและการจัดการที่เหมาะกับลักษณะพื้นที่",
    )

    para1 = (
        f"<p>{description}</p>"
        if description
        else f"<p>บริการ <strong>{keyword}</strong> จาก <strong>Sangkan Clean</strong> "
        f"ออกแบบมาสำหรับ{place['label']} ที่ต้องการมาตรฐานความสะอาดที่ตรวจสอบได้</p>"
    )
    para2 = (
        f"<p>ปัญหาที่พบบ่อยใน{place['label']}คือ {place['pain']} "
        f"บริการ <strong>{keyword}</strong> จึงเน้น{place['focus']} "
        f"โดยทีมงานมืออาชีพที่มีขั้นตอนชัดเจน ไม่ทำงานแบบสุ่มพื้นที่</p>"
    )
    para3 = (
        f"<p>สำหรับแนวทางของเรา ({service['label']}) {service['method']} "
        f"ลูกค้าสามารถวางแผนล่วงหน้า รู้ขอบเขตงาน และตรวจรับผลลัพธ์หลังส่งมอบได้อย่างมั่นใจ</p>"
    )
    para4 = (
        f"<p><strong>Sangkan Clean</strong> พร้อมประเมินหน้างานและเสนอแนวทางที่เหมาะกับ "
        f"<strong>{keyword}</strong> ทั้งงานครั้งเดียวและงานต่อเนื่อง "
        f"เพื่อให้{place['label']}กลับมาน่าใช้และพร้อมสร้างภาพลักษณ์ที่ดี</p>"
    )

    stats = (
        f"<p>{place['stat']} — <em>ข้อมูลโดยประมาณจากแนวโน้มอุตสาหกรรม</em></p>"
        f"<p>การลงทุนในบริการทำความสะอาดมืออาชีพจึงไม่ใช่แค่เรื่องความสวยงาม "
        f"แต่เกี่ยวกับสุขอนามัย ความปลอดภัย และความน่าเชื่อถือของพื้นที่ใช้งาน</p>"
    )

    takeaway_html = "".join(
        f"<li>{item}</li>" for item in takeaways
    )
    faq_html = "".join(
        f"<h3>{q}</h3><p>{a}</p>" for q, a in faq_items
    )

    return f"""<article>
  <h2>{GEO_MARKER} (Key Takeaways)</h2>
  <ul>
    {takeaway_html}
  </ul>

  <h2>เนื้อหาหลัก</h2>
  {para1}
  {para2}
  {para3}
  {para4}

  <h2>ข้อมูลสถิติที่น่าสนใจ</h2>
  {stats}

  <h2>คำถามที่พบบ่อย (FAQ)</h2>
  {faq_html}
</article>
"""


def mark_legacy_gemini(posts: list[dict]) -> int:
    """Posts that already have GEO but no source were from earlier API runs."""
    n = 0
    for post in posts:
        if GEO_MARKER in post.get("content", "") and not post.get("geo_source"):
            post["geo_source"] = "gemini"
            n += 1
    return n


def upgrade_offline(limit: int = 0) -> dict[str, int]:
    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    legacy = mark_legacy_gemini(posts)
    pending = [i for i, p in enumerate(posts) if needs_offline_upgrade(p)]
    if limit > 0:
        pending = pending[:limit]

    upgraded = 0
    today = date.today().isoformat()
    for idx in pending:
        post = posts[idx]
        slug = post.get("slug") or slugify(post["title"]) or f"post-{idx}"
        post["slug"] = slug
        post["content"] = build_geo_html(post["title"], post.get("description", ""), slug)
        post["dateModified"] = today
        post["geo_source"] = "offline"
        upgraded += 1
        print(f"[offline] {upgraded}/{len(pending)} -> {post['title'][:60]}", flush=True)

    with open("posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    if upgraded:
        print("Building blog HTML…", flush=True)
        import build_site

        build_site.rebuild_blog_surface()

    geo_total = sum(1 for p in posts if GEO_MARKER in p.get("content", ""))
    gemini = sum(1 for p in posts if p.get("geo_source") == "gemini")
    offline = sum(1 for p in posts if p.get("geo_source") == "offline")
    return {
        "upgraded": upgraded,
        "legacy_marked_gemini": legacy,
        "geo_total": geo_total,
        "gemini": gemini,
        "offline": offline,
        "total": len(posts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart offline GEO upgrade (no API)")
    parser.add_argument("--limit", type=int, default=0, help="Max posts (0=all pending)")
    args = parser.parse_args()
    stats = upgrade_offline(limit=args.limit)
    print(
        f"DONE upgraded={stats['upgraded']} "
        f"geo={stats['geo_total']}/{stats['total']} "
        f"gemini={stats['gemini']} offline={stats['offline']} "
        f"legacy_marked={stats['legacy_marked_gemini']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
