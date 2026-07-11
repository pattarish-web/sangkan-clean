"""Rotating topics for daily social content."""

from __future__ import annotations

# format: "video" ~40% (Ken Burns clips for FB/IG Reels); "image" for still posts.
# TikTok always gets a 9:16 clip regardless of format.
VIDEO_TOPIC_IDS = frozenset(
    {"office_ondemand", "agency_focus", "price_pack", "affiliate"}
)

TOPICS: list[dict[str, str]] = [
    {
        "id": "office_ondemand",
        "label": "แม่บ้านออฟฟิศ On-Demand",
        "angle": "ไม่ต้องจ้างประจำ เรียกใช้ตามต้องการ โซนอุดมสุข–บางนา",
        "headline": "ออฟฟิศสะอาด โดยไม่จ้างประจำ",
        "format": "video",
    },
    {
        "id": "agency_focus",
        "label": "เอเจนซี่ / ทีมครีเอทีฟ",
        "angle": "ทีมโฟกัสงาน ไม่ต้องจัดเวรแม่บ้านเอง มี QC และคนสำรอง",
        "headline": "เอเจนซี่โฟกัสงาน เราดูแลความสะอาด",
        "format": "video",
    },
    {
        "id": "tech_team",
        "label": "บริษัท Tech / สตาร์ทอัพ",
        "angle": "GPS check-in รายงานรูปก่อน–หลัง lean operations",
        "headline": "Tech team ต้องการออฟฟิศที่พร้อมทำงาน",
        "format": "image",
    },
    {
        "id": "big_cleaning",
        "label": "Big Cleaning",
        "angle": "ทำความสะอาดครั้งใหญ่ ขจัดคราบฝังลึก ทีมมืออาชีพ 30+ ปี",
        "headline": "Big Cleaning ที่จบงานจริง",
        "format": "image",
    },
    {
        "id": "maid_backup",
        "label": "แม่บ้านประจำ + คนสำรอง",
        "angle": "ทำงานในนามบริษัท มีทีม QC และคนทดแทนเมื่อลา",
        "headline": "แม่บ้านประจำ ที่ไม่ทิ้งงานกลางคัน",
        "format": "image",
    },
    {
        "id": "service_area",
        "label": "พื้นที่บริการ",
        "angle": "กรุงเทพฯ นนทบุรี สมุทรปราการ ปทุมธานี ชลบุรี ระยอง",
        "headline": "ทำความสะอาดครอบคลุมโซนที่คุณอยู่",
        "format": "image",
    },
    {
        "id": "price_pack",
        "label": "แพ็ค S / M ออฟฟิศ",
        "angle": "S ฿2,900 / M ฿6,900 ต่อเดือน เหมาะโฮมออฟฟิศและเอเจนซี่",
        "headline": "แพ็คแม่บ้านออฟฟิศ เริ่มต้นชัดเจน",
        "format": "video",
    },
    {
        "id": "affiliate",
        "label": "ชวนเพื่อนรับเครดิต",
        "angle": "ชวนเพื่อนในโซน รับเครดิตคืน 10% ของยอด สะสมถึงสิ้นปี",
        "headline": "ชวนเพื่อนในโซน รับเครดิตคืน",
        "format": "video",
    },
    {
        "id": "after_construction",
        "label": "หลังก่อสร้าง",
        "angle": "ฝุ่นปูน คราบสี งานละเอียดก่อนเข้าอยู่หรือเปิดร้าน",
        "headline": "หลังก่อสร้าง — เราจัดการฝุ่นและคราบ",
        "format": "image",
    },
    {
        "id": "soft_cleaning",
        "label": "Soft Cleaning",
        "angle": "ดูแลความสะอาดประจำ อ่อนโยนกับพื้นผิว ออฟฟิศและคอนโด",
        "headline": "Soft Cleaning ดูแลความสะอาดประจำ",
        "format": "image",
    },
]


def pick_topic(last_id: str | None) -> dict[str, str]:
    if not last_id:
        return TOPICS[0]
    ids = [t["id"] for t in TOPICS]
    try:
        idx = ids.index(last_id)
    except ValueError:
        return TOPICS[0]
    return TOPICS[(idx + 1) % len(TOPICS)]
