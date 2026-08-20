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
    # Official page (new) — keep in sync with index.html sameAs / float CTAs
    "facebook": "https://www.facebook.com/61592039062581",
    "messenger": "https://m.me/61592039062581",
    "email": FORM_SUBMIT_EMAIL,
    # HQ: 13°38'41.0"N 100°26'25.5"E → แขวงแสมดำ เขตบางขุนเทียน กรุงเทพฯ 10150
    "latitude": 13.644722,
    "longitude": 100.440417,
    "maps_url": "https://maps.google.com/?q=13.644722,100.440417",
    "street_address": "แขวงแสมดำ เขตบางขุนเทียน",
    "address_locality": "กรุงเทพมหานคร",
    "address_region": "กรุงเทพมหานคร",
    "postal_code": "10150",
    "address_country": "TH",
}

# Canonical URL policy (GitHub Pages, long-term host):
# - Homepage: https://www.sangkanclean.com/  (not /index.html)
# - Other pages: keep .html in canonical + sitemap (matches files + internal links)
# - Extensionless URLs are GH Pages aliases of the same .html file; do not create
#   a second canonical form. Soft HTML stubs handle cannibalization (no true 301).

SERVICE_LANDINGS = [
    {
        "file": "landing-softcleaning",
        "title": "บริการ Soft Cleaning ทำความสะอาดเฉพาะจุด",
        "description": "Soft Cleaning ดูแลความสะอาดประจำ อ่อนโยนกับพื้นผิว เหมาะสำนักงาน คอนโด ร้านค้า ราคาเริ่มต้น 3,500 บาท",
        "price": "เริ่มต้น ฿3,500",
        "icon": "fa-hand-sparkles",
        "intro": "Soft Cleaning ของ Sangkan Clean คือการทำความสะอาดแบบอ่อนโยน เน้นพื้นผิวที่บอบบางและพื้นที่ใช้งานประจำวัน เหมาะกับออฟฟิศ คอนโด ร้านค้า ที่ต้องการความสะอาดต่อเนื่องโดยไม่ทำลายวัสดุ",
        "suitable_html": "<li>สำนักงานและ co-working ที่ต้องการดูแลรายสัปดาห์/รายเดือน</li><li>คอนโดและพื้นที่ส่วนกลางที่ผิววัสดุบอบบาง</li><li>ร้านค้า คลินิก หรือโชว์รูมที่ต้องการภาพลักษณ์สะอาดสม่ำเสมอ</li>",
        "process_html": "<li>สำรวจพื้นที่และจุดเสี่ยงคราบ/ฝุ่น</li><li>ทำความสะอาดตามโซนด้วยน้ำยาและอุปกรณ์ที่เหมาะกับพื้นผิว</li><li>เช็ดเงาจุดสัมผัสบ่อย เช่น มือจับ โต๊ะ กระจกภายใน</li><li>ตรวจคุณภาพก่อนส่งมอบและนัดรอบถัดไป</li>",
        "includes_html": "<li>อุปกรณ์และน้ำยาอ่อนโยนต่อพื้นผิว</li><li>แผนงานตามขนาดพื้นที่และความถี่ที่ตกลง</li>",
        "faq1_q": "Soft Cleaning ต่างจาก Big Cleaning อย่างไร?",
        "faq1_a": "Soft Cleaning เน้นดูแลประจำและพื้นผิวบอบบาง ส่วน Big Cleaning เป็นการทำความสะอาดเชิงลึกครั้งใหญ่สำหรับคราบฝังลึกหรือพื้นที่โรงงาน/อาคาร",
        "faq2_q": "Soft Cleaning ราคาเท่าไหร่?",
        "faq2_a": "เริ่มต้น ฿3,500 ประเมินตามขนาดพื้นที่และความถี่ โทร 063-686-5134 หรือ LINE @sangkanclean",
        "faq3_q": "ต้องเตรียมอุปกรณ์เองหรือไม่?",
        "faq3_a": "ไม่ต้องครับ ทีมงานเตรียมอุปกรณ์และน้ำยามาตรฐานมาให้ครบ รวมประกันความเสียหายจากการปฏิบัติงาน",
    },
    {
        "file": "landing-glass",
        "title": "บริการเช็ดกระจกอาคารสูง",
        "description": "เช็ดกระจกอาคารสูงด้วยอุปกรณ์มาตรฐานความปลอดภัย ทีมงานมืออาชีพ ครอบคลุมกรุงเทพและปริมณฑล",
        "price": "สอบถามราคา",
        "icon": "fa-building",
        "intro": "บริการเช็ดกระจกอาคารสูงของ Sangkan Clean ใช้ทีมงานที่ผ่านการฝึกด้านความปลอดภัย พร้อมอุปกรณ์โรยตัว/กระเช้าตามลักษณะอาคาร เพื่อให้กระจกใสและอาคารดูใหม่โดยไม่กระทบการใช้งานภายใน",
        "suitable_html": "<li>อาคารสำนักงานและคอนโดสูง</li><li>โชว์รูม ห้างสรรพสินค้า และ lobby กระจกขนาดใหญ่</li><li>งานบำรุงรักษาตามรอบหรือก่อนส่งมอบโครงการ</li>",
        "process_html": "<li>สำรวจความสูง จุดยึด และแผนความปลอดภัย</li><li>จัดทีมและอุปกรณ์ให้เหมาะกับอาคาร</li><li>ทำความสะอาดกระจกและขอบเฟรมตามโซน</li><li>ตรวจความเรียบร้อยและเก็บงานพื้นด้านล่าง</li>",
        "includes_html": "<li>อุปกรณ์ความปลอดภัยมาตรฐานงานสูง</li><li>น้ำยาเช็ดกระจกที่เหมาะกับงานอาคาร</li>",
        "faq1_q": "เช็ดกระจกอาคารสูงคิดราคาอย่างไร?",
        "faq1_a": "คิดตามความสูง พื้นที่กระจก และความยากของหน้างาน ประเมินหน้างานฟรี โทร 063-686-5134 หรือ LINE @sangkanclean",
        "faq2_q": "ทำได้ช่วงนอกเวลาทำการไหม?",
        "faq2_a": "ได้ครับ จัดคิวนอกเวลาหรือวันหยุดได้เมื่อแจ้งล่วงหน้า เพื่อไม่รบกวนผู้ใช้งานอาคาร",
        "faq3_q": "มีมาตรการความปลอดภัยอย่างไร?",
        "faq3_a": "ใช้ทีมงานที่ผ่านการฝึก อุปกรณ์นิรภัยครบ และวางแผนหน้างานก่อนเริ่มทุกครั้ง",
    },
    {
        "file": "landing-carpet",
        "title": "บริการซักพรม โซฟา ผ้าม่าน",
        "description": "ซักแห้งพรม โซฟา เก้าอี้ ผ้าม่าน ขจัดคราบ กลิ่นอับ ไรฝุ่น อย่างล้ำลึก ราคาเริ่มต้น 800 บาท",
        "price": "เริ่มต้น ฿800",
        "icon": "fa-couch",
        "intro": "บริการซักพรม โซฟา เก้าอี้ และผ้าม่านของ Sangkan Clean ช่วยขจัดคราบ กลิ่นอับ และไรฝุ่น ด้วยวิธีที่เหมาะกับชนิดผ้า/พรม ไม่ทิ้งความชื้นแฉะ และพร้อมใช้งานได้เร็วขึ้น",
        "suitable_html": "<li>พรมสำนักงาน โถงรับแขก และห้องประชุม</li><li>โซฟา เก้าอี้ผ้า ในบ้าน คอนโด โรงแรม</li><li>ผ้าม่านที่สะสมฝุ่นและกลิ่น</li>",
        "process_html": "<li>ตรวจชนิดผ้า/พรมและจุดคราบ</li><li>ดูดฝุ่นและเตรียมพื้นผิวก่อนซัก</li><li>ซัก/ทำความสะอาดตามวิธีที่เหมาะสม</li><li>จัดการความชื้นและตรวจกลิ่นก่อนส่งมอบ</li>",
        "includes_html": "<li>น้ำยาขจัดคราบและฆ่าเชื้อตามความเหมาะสม</li><li>อุปกรณ์ดูดฝุ่น/ซักเฉพาะงานผ้าและพรม</li>",
        "faq1_q": "ซักพรม โซฟา ผ้าม่าน ราคาเท่าไหร่?",
        "faq1_a": "เริ่มต้น ฿800 ขึ้นกับขนาดและชนิดวัสดุ ประเมินหน้างานฟรี โทร 063-686-5134 หรือ LINE @sangkanclean",
        "faq2_q": "แห้งกี่ชั่วโมงหลังซัก?",
        "faq2_a": "โดยทั่วไปใช้งานได้ภายในหลายชั่วโมง ขึ้นกับชนิดผ้าและความชื้นในพื้นที่ ทีมงานจะแนะนำวิธีดูแลหลังซักให้",
        "faq3_q": "ขจัดไรฝุ่นและกลิ่นอับได้จริงไหม?",
        "faq3_a": "ได้ครับ เน้นทำความสะอาดเชิงลึกร่วมกับน้ำยาที่เหมาะสม และแนะนำการดูแลต่อเนื่องเพื่อลดการสะสมซ้ำ",
    },
    {
        "file": "landing-ozone",
        "title": "บริการอบโอโซนฆ่าเชื้อ",
        "description": "อบโอโซนฆ่าเชื้อโรค แบคทีเรีย ไวรัส กำจัดกลิ่นอับ มาตรฐานปลอดภัย ราคาเริ่มต้น 1,200 บาท",
        "price": "เริ่มต้น ฿1,200",
        "icon": "fa-atom",
        "intro": "บริการอบโอโซนของ Sangkan Clean ช่วยลดเชื้อโรคและกลิ่นอับในพื้นที่ปิด เช่น ออฟฟิศ ห้องพัก คอนโด รถ หรือพื้นที่หลังน้ำท่วม/ปรับปรุง โดยทีมงานควบคุมเวลาและความเข้มข้นให้เหมาะสม",
        "suitable_html": "<li>พื้นที่ที่มีกลิ่นอับ กลิ่นบุหรี่ หรือกลิ่นสัตว์เลี้ยง</li><li>ห้องพัก โรงแรม ออฟฟิศหลังปรับปรุง</li><li>งานฆ่าเชื้อเสริมหลังทำความสะอาดใหญ่</li>",
        "process_html": "<li>ประเมินขนาดห้องและจุดกำเนิดกลิ่น/ความเสี่ยง</li><li>เตรียมพื้นที่และแจ้งข้อควรระวังระหว่างอบ</li><li>เดินเครื่องอบโอโซนตามเวลาที่เหมาะสม</li><li>ระบายอากาศและตรวจกลิ่นก่อนส่งมอบ</li>",
        "includes_html": "<li>เครื่องอบโอโซนและอุปกรณ์วัด/ควบคุมเวลา</li><li>คำแนะนำการใช้งานพื้นที่หลังอบ</li>",
        "faq1_q": "อบโอโซนราคาเท่าไหร่?",
        "faq1_a": "เริ่มต้น ฿1,200 ตามขนาดพื้นที่ โทร 063-686-5134 หรือ LINE @sangkanclean เพื่อประเมิน",
        "faq2_q": "คนและสัตว์เลี้ยงอยู่ระหว่างอบได้ไหม?",
        "faq2_a": "ไม่ควรอยู่ระหว่างอบ ทีมงานจะแจ้งระยะเวลาและให้เข้าพื้นที่ได้เมื่อระบายอากาศเรียบร้อย",
        "faq3_q": "ใช้ร่วมกับ Big Cleaning ได้ไหม?",
        "faq3_a": "ได้ครับ นิยมทำหลังทำความสะอาดเชิงลึกเพื่อลดกลิ่นและเสริมสุขอนามัย",
    },
]

LOCAL_AREAS = [
    {
        "slug": "กรุงเทพมหานคร",
        "file": "local-bangkok",
        "title": "บริการทำความสะอาด กรุงเทพมหานคร",
        "description": "Sangkan Clean รับทำความสะอาด Big Cleaning และจัดหาแม่บ้านประจำในกรุงเทพฯ ทุกเขต สุขุมวิท สีลม บางนา ลาดพร้าว รามอินทรา",
        "districts": "สุขุมวิท, สีลม, สาทร, รัชดา, ลาดพร้าว, บางนา, ปิ่นเกล้า, รามอินทรา, ฝั่งธนบุรี และทุกเขตพื้นที่",
        "latitude": "13.7563",
        "longitude": "100.5018",
        "geo_region": "TH-10",
        "placename": "Bangkok",
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
        "latitude": "13.8621",
        "longitude": "100.5144",
        "geo_region": "TH-12",
        "placename": "Nonthaburi",
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
        "latitude": "13.5990",
        "longitude": "100.5998",
        "geo_region": "TH-11",
        "placename": "Samut Prakan",
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
        "latitude": "14.0208",
        "longitude": "100.5250",
        "geo_region": "TH-13",
        "placename": "Pathum Thani",
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
        "latitude": "13.3611",
        "longitude": "100.9847",
        "geo_region": "TH-20",
        "placename": "Chonburi",
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
        "latitude": "13.7563",
        "longitude": "100.5018",
        "geo_region": "TH",
        "placename": "Thailand",
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
