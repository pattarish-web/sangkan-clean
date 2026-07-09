"""Shared site configuration."""

import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

SITE_URL = "https://www.sangkanclean.com"
# Set in site_config or via env GA4_MEASUREMENT_ID (e.g. GitHub Actions secret)
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID", "G-MJG0VZPFKS")
ADS_CONVERSION_ID = "AW-18299765093"
# Google Ads conversion labels — create in Ads → Goals → Conversions → Website
ADS_PHONE_CONVERSION_LABEL = os.environ.get(
    "ADS_PHONE_CONVERSION_LABEL", "XIKsCOeMw80cEOWCgZZE"
)
ADS_LINE_CONVERSION_LABEL = os.environ.get(
    "ADS_LINE_CONVERSION_LABEL", "ahW4CM6qxs0cEOWCgZZE"
)
ADS_LEAD_CONVERSION_LABEL = os.environ.get("ADS_LEAD_CONVERSION_LABEL", "")
FORM_SUBMIT_EMAIL = "info@sangkanclean.com"


def ads_conversion_send_to(label: str) -> str:
    """Build gtag send_to value AW-xxx/LABEL."""
    if not label:
        return ""
    return f"{ADS_CONVERSION_ID}/{label}"


def ads_conversion_labels_js() -> str:
    """JSON map of conversion kinds → send_to for inline gtag bootstrap."""
    mapping = {
        "phone": ads_conversion_send_to(ADS_PHONE_CONVERSION_LABEL),
        "line": ads_conversion_send_to(ADS_LINE_CONVERSION_LABEL),
        "lead": ads_conversion_send_to(ADS_LEAD_CONVERSION_LABEL),
    }
    return json.dumps(mapping, ensure_ascii=False)

BUSINESS = {
    "phone": "+66636865134",
    "phone_display": "063-686-5134",
    "line": "https://line.me/ti/p/@sangkanclean",
    "facebook": "https://www.facebook.com/100067763717435",
    "messenger": "https://m.me/100067763717435",
    "email": FORM_SUBMIT_EMAIL,
    "latitude": 13.7563,
    "longitude": 100.5018,
    "maps_url": "https://maps.google.com/?q=13.7563,100.5018",
}

SERVICE_LANDINGS = [
    {
        "file": "landing-softcleaning",
        "title": "บริการ Soft Cleaning ทำความสะอาดเฉพาะจุด",
        "description": "Soft Cleaning ดูแลความสะอาดประจำ อ่อนโยนกับพื้นผิว เหมาะสำนักงาน คอนโด ร้านค้า ราคาเริ่มต้น 3,500 บาท",
        "price": "เริ่มต้น ฿3,500",
        "icon": "fa-hand-sparkles",
    },
    {
        "file": "landing-glass",
        "title": "บริการเช็ดกระจกอาคารสูง",
        "description": "เช็ดกระจกอาคารสูงด้วยอุปกรณ์มาตรฐานความปลอดภัย ทีมงานมืออาชีพ ครอบคลุมกรุงเทพและปริมณฑล",
        "price": "สอบถามราคา",
        "icon": "fa-building",
    },
    {
        "file": "landing-carpet",
        "title": "บริการซักพรม โซฟา ผ้าม่าน",
        "description": "ซักแห้งพรม โซฟา เก้าอี้ ผ้าม่าน ขจัดคราบ กลิ่นอับ ไรฝุ่น อย่างล้ำลึก ราคาเริ่มต้น 800 บาท",
        "price": "เริ่มต้น ฿800",
        "icon": "fa-couch",
    },
    {
        "file": "landing-ozone",
        "title": "บริการอบโอโซนฆ่าเชื้อ",
        "description": "อบโอโซนฆ่าเชื้อโรค แบคทีเรีย ไวรัส กำจัดกลิ่นอับ มาตรฐานปลอดภัย ราคาเริ่มต้น 1,200 บาท",
        "price": "เริ่มต้น ฿1,200",
        "icon": "fa-atom",
    },
]

LOCAL_AREAS = [
    {
        "slug": "กรุงเทพมหานคร",
        "file": "local-bangkok",
        "title": "บริการทำความสะอาด กรุงเทพมหานคร",
        "description": "Sangkan Clean รับทำความสะอาด Big Cleaning และจัดหาแม่บ้านประจำในกรุงเทพฯ ทุกเขต สุขุมวิท สีลม บางนา ลาดพร้าว รามอินทรา",
        "districts": "สุขุมวิท, สีลม, สาทร, รัชดา, ลาดพร้าว, บางนา, ปิ่นเกล้า, รามอินทรา, ฝั่งธนบุรี และทุกเขตพื้นที่",
        "faq": [
            ("รับทำความสะอาดในกรุงเทพเขตไหนบ้าง?", "ครอบคลุมทุกเขตในกรุงเทพมหานคร รวมสุขุมวิท สีลม บางนา ลาดพร้าว รามอินทรา และฝั่งธนบุรี"),
            ("จองคิว Big Cleaning ในกรุงเทพใช้เวลากี่วัน?", "แนะนำจองล่วงหน้า 2-3 วัน กรณีด่วนโทรสอบถามคิวได้ที่ 063-686-5134"),
            ("มีทีมงานกี่คนต่อโปรเจกต์?", "ขึ้นกับขนาดพื้นที่ โดยทั่วไป Big Cleaning 2-4 คน พร้อมหัวหน้าทีมควบคุมคุณภาพ"),
        ],
    },
    {
        "slug": "นนทบุรี",
        "file": "local-nonthaburi",
        "title": "บริการทำความสะอาด นนทบุรี",
        "description": "บริการทำความสะอาดโรงงาน ออฟฟิศ คอนโด และแม่บ้านประจำในนนทบุรี ครอบคลุมเมืองนนทบุรี ปากเกร็ด บางใหญ่",
        "districts": "เมืองนนทบุรี, ปากเกร็ด, บางใหญ่, บางบัวทอง, บางกรวย",
        "faq": [
            ("รับงานในนนทบุรีเขตไหนบ้าง?", "เมืองนนทบุรี ปากเกร็ด บางใหญ่ บางบัวทอง และบางกรวย"),
            ("มีบริการแม่บ้านประจำในนนทบุรีไหม?", "มีครับ จัดหาแม่บ้านประจำสำนักงานและคอนโด พร้อมคนสำรองทดแทน"),
            ("คิดค่าเดินทางเพิ่มไหม?", "พื้นที่ปริมณฑลใกล้กรุงเทพ ประเมินตามระยะทางและขนาดงาน แจ้งราคาชัดเจนก่อนเริ่มงาน"),
        ],
    },
    {
        "slug": "สมุทรปราการ",
        "file": "local-samut-prakan",
        "title": "บริการทำความสะอาด สมุทรปราการ",
        "description": "รับทำความสะอาดโรงงาน โกดัง ออฟฟิศ และ Big Cleaning ในสมุทรปราการ บางพลี พระประแดง",
        "districts": "เมืองสมุทรปราการ, บางพลี, พระประแดง, สำโรง, บางบ่อ",
        "faq": [
            ("รับทำความสะอาดโรงงานในสมุทรปราการไหม?", "รับครับ โรงงาน โกดัง นิคมอุตสาหกรรม พร้อมอุปกรณ์ระดับอุตสาหกรรม"),
            ("ทีมงานผ่านการอบรมมาตรฐานโรงงานไหม?", "ผ่านการฝึกอบรมด้านความปลอดภัยและสุขอนามัยในโรงงาน"),
            ("ให้บริการวันหยุดได้ไหม?", "ได้ครับ จัดทีมตามคิวงาน รวมงานด่วนและวันหยุดนักขัตฤกษ์"),
        ],
    },
    {
        "slug": "ปทุมธานี",
        "file": "local-pathum-thani",
        "title": "บริการทำความสะอาด ปทุมธานี",
        "description": "บริการทำความสะอาดครบวงจรในปทุมธานี รังสิต ลำลูกกา คลองหลวง โรงงานและออฟฟิศ",
        "districts": "รังสิต, ลำลูกกา, คลองหลวง, เมืองปทุมธานี, ธัญบุรี",
        "faq": [
            ("รับงานในรังสิตและลำลูกกาไหม?", "รับครับ ครอบคลุมรังสิต ลำลูกกา คลองหลวง และเมืองปทุมธานี"),
            ("มีบริการหลังก่อสร้างในปทุมธานีไหม?", "มีครับ ทำความสะอาดหลังก่อสร้าง คอนโด ออฟฟิศ โรงงาน"),
            ("ประเมินราคาฟรีไหม?", "ประเมินราคาเบื้องต้นฟรี ไม่มีข้อผูกมัด"),
        ],
    },
    {
        "slug": "ระยอง-ชลบุรี",
        "file": "local-rayong-chonburi",
        "title": "บริการทำความสะอาด ระยอง ชลบุรี",
        "description": "รับงานทำความสะอาดโรงงาน นิคมอุตสาหกรรม อมตะนคร มาบตาพุด และศรีราชา",
        "districts": "นิคมอุตสาหกรรม, อมตะนคร, มาบตาพุด, เมืองชลบุรี, ศรีราชา",
        "faq": [
            ("รับงานในนิคมอุตสาหกรรมอมตะนครไหม?", "รับครับ โรงงานและอาคารสำนักงานในนิคมอุตสาหกรรมชลบุรีและระยอง"),
            ("เดินทางจากกรุงเทพใช้เวลานานไหม?", "จัดทีมตามพื้นที่งาน นัดหมายและเริ่มงานตามเวลาที่ตกลง"),
            ("รับโปรเจกต์ขนาดใหญ่ทั่วประเทศไหม?", "รับครับ โรงงาน ห้างสรรพสินค้า โรงแรม ทั่วประเทศ"),
        ],
    },
    {
        "slug": "ทั่วประเทศ",
        "file": "local-nationwide",
        "title": "บริการทำความสะอาด ทั่วประเทศไทย",
        "description": "รับโปรเจกต์ Big Cleaning โรงงาน อาคาร และห้างสรรพสินค้าทั่วประเทศ",
        "districts": "โรงงาน อาคารสำนักงาน ห้างสรรพสินค้า โรงแรม โรงพยาบาล",
        "faq": [
            ("รับงานต่างจังหวัดไหม?", "รับครับ โปรเจกต์ขนาดใหญ่ทั่วประเทศ โรงงาน ห้าง โรงแรม"),
            ("มีทีมงานในพื้นที่ไหม?", "ประสานทีมงานในพื้นที่หรือส่งทีมจากกรุงเทพตามขนาดโปรเจกต์"),
            ("ต้องจองล่วงหน้ากี่วัน?", "โปรเจกต์ใหญ่แนะนำจองล่วงหน้า 1-2 สัปดาห์"),
        ],
    },
]


def _has_ga4():
    return bool(GA4_MEASUREMENT_ID and GA4_MEASUREMENT_ID != "G-PLACEHOLDER")


def analytics_script_tag(prefix=""):
    """Return standard Google gtag snippet for <head>; prefix is '' or '../'."""
    # Load gtag.js via Ads ID (always valid). GA4 G- IDs may 404 until property propagates.
    ga4_config = f"  gtag('config', '{GA4_MEASUREMENT_ID}');\n" if _has_ga4() else ""
    labels_json = ads_conversion_labels_js()
    return f"""<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={ADS_CONVERSION_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  window.gtag = gtag;
  gtag('js', new Date());
{ga4_config}  gtag('config', '{ADS_CONVERSION_ID}');
  window.adsConversions = {labels_json};
  window.adsLeadSendTo = window.adsConversions.phone || window.adsConversions.lead || window.adsConversions.line || '';
</script>"""
