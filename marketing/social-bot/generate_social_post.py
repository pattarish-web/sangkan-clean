"""Daily social content orchestrator — image + short video mix."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
for p in (str(ROOT), str(REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)

from compose_image import save_feed, save_stories  # noqa: E402
from creative_standard import (  # noqa: E402
    SUBLINE_MAX,
    THAI_TONE_RULES,
    build_background_prompt,
    clip_subline,
)
from render_video import (  # noqa: E402
    has_ffmpeg,
    render_feed_clip,
    render_stories_clip,
)
from topics import pick_topic  # noqa: E402

LOG_PATH = ROOT / "log.json"
OUT_DIR = ROOT / "out"

SITE = "https://www.sangkanclean.com"
LINE_OA = "@sangkanclean"
PHONE = "063-686-5134"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _channels() -> set[str]:
    raw = os.environ.get("CHANNELS", "facebook,instagram,tiktok,line").strip()
    return {c.strip().lower() for c in raw.split(",") if c.strip()}


def _load_log() -> dict:
    if not LOG_PATH.exists():
        return {"last_topic": None, "posts": []}
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_topic": None, "posts": []}


def _save_log(data: dict) -> None:
    LOG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_seo_keywords() -> list[str]:
    """Load SEO keywords from keywords.json database."""
    path = REPO / "seo" / "keywords.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [item["keyword"] for item in data if isinstance(item, dict) and "keyword" in item]
    except Exception as e:
        print(f"Error loading keywords: {e}")
        return []


def _pick_seo_keywords(topic: dict, all_keywords: list[str], limit: int = 3) -> list[str]:
    """Select relevant SEO keywords based on topic context."""
    matched = []
    topic_id = str(topic.get("id", "")).lower()
    topic_label = str(topic.get("label", "")).lower()

    for kw in all_keywords:
        kw_lower = kw.lower()
        if any(w in topic_id or w in topic_label for w in ["construction", "ก่อสร้าง", "รีโนเวท", "renovate"]):
            if any(k in kw_lower for k in ["ก่อสร้าง", "รีโนเวท", "บิ๊กคลีนนิ่ง"]):
                matched.append(kw)
        elif any(w in topic_id or w in topic_label for w in ["office", "agency", "tech", "ออฟฟิศ"]):
            if any(k in kw_lower for k in ["ออฟฟิศ", "สำนักงาน", "แม่บ้าน"]):
                matched.append(kw)
        elif any(w in topic_id or w in topic_label for w in ["home", "condo", "คอนโด", "บ้าน"]):
            if any(k in kw_lower for k in ["บ้าน", "คอนโด", "ทำความสะอาดบ้าน"]):
                matched.append(kw)
        elif any(w in topic_id or w in topic_label for w in ["clean", "maid"]):
            if any(k in kw_lower for k in ["แม่บ้าน", "ทำความสะอาด"]):
                matched.append(kw)

    if not matched:
        matched = all_keywords[:limit]
    return list(set(matched))[:limit]


def _fallback_captions(topic: dict) -> dict:
    hl = topic["headline"]
    angle = topic["angle"]
    is_edu = topic.get("type") == "edu"

    if is_edu:
        sign_off = "— เกร็ดความรู้จาก Sangkan Clean"
        return {
            "fb_ig": f"{hl}\n\n{angle}\n\n{sign_off}",
            "tiktok": f"{hl}\n{angle}\n{sign_off}",
            "line": f"{hl}\n\n{angle}\n\n{sign_off}",
            "image_subline": clip_subline(angle),
            "voiceover_text": f"รู้ไหมคะว่า {hl}? แอดมิน มีข้อมูล ดีๆ มาฝากค่ะ. {angle}. เพื่อสุขภาพ และ ความสะอาด ของออฟฟิศ อย่าลืม ใส่ใจ เรื่องนี้ นะคะ",
            "hashtags": ["#SangkanClean", "#ความรู้ทำความสะอาด", "#OfficeCleanTips"],
        }

    cta = f"ทัก LINE {LINE_OA} หรือดูรายละเอียดที่ {SITE}"
    return {
        "fb_ig": (
            f"{hl}\n\n{angle}\n\n"
            f"Sangkan Clean — คลีนออฟฟิศให้ทีมวัยใหม่ เอเจนซี่ และเทค\n"
            f"{cta}\nโทร {PHONE}"
        ),
        "tiktok": f"{hl}\n{angle}\nLINE {LINE_OA}",
        "line": f"{hl}\n\n{angle}\n\nทักไลน์ {LINE_OA} ได้เลย",
        "image_subline": clip_subline(angle),
        "voiceover_text": f"ใครกำลัง เจอปัญหา {hl} บ้างคะ? สั่งการ คลีน ตัวจริง เรื่องความสะอาด พร้อมดูแล ออฟฟิศคุณ ให้เนี้ยบ ในทุกตารางนิ้ว. ทักไลน์ {LINE_OA} ได้เลยค่ะ",
        "hashtags": ["#SangkanClean", "#แม่บ้านออฟฟิศ", "#BigCleaning"],
    }


def _build_prompt(topic: dict, keywords: list[str] = None) -> str:
    """Build the AI prompt — different for edu vs promo content."""
    is_edu = topic.get("type") == "edu"
    kw_str = ", ".join(keywords) if keywords else "แม่บ้านทำความสะอาด"

    seo_geo_rules = (
        f"** กฎการเขียนตามหลัก SEO / AIO / GEO (สำคัญมาก) **\n"
        f"1. แทรกคีย์เวิร์ดเหล่านี้อย่างเป็นธรรมชาติห้ามยัดเยียด: {kw_str}\n"
        f"2. โครงสร้างคอนเทนต์ต้องมีความชัดเจนและน่าเชื่อถือสูง เพื่อให้ AI Search Engines นำไปประมวลผลต่อได้ง่าย\n"
        f"3. หลีกเลี่ยงประโยคที่ซับซ้อนเกินไป เน้นข้อมูลที่เป็นประโยชน์จริง\n"
        f"4. บทพากย์ (voiceover_text) ต้องมีความเป็นธรรมชาติสูงมาก เหมือนเพื่อนร่วมงานหรือคนจริงๆ เล่าสู่กันฟัง ชวนคุยอย่างเป็นกันเองและลื่นไหล ห้ามใช้สำนวนการพากย์โฆษณาที่แข็งทู่หรือสำนวนแปลจากต่างประเทศ ห้ามมีคำฟุ่มเฟือยของบอตเด็ดขาด\n"
        f"5. สำคัญที่สุด: ให้ใส่เว้นวรรค (space) ระหว่างวลีสั้นๆ ในบทพากย์เป็นระยะๆ (เช่น ทุกๆ 10-15 ตัวอักษร) เพื่อเว้นจังหวะให้เสียง AI หายใจได้เป็นธรรมชาติ และช่วยให้ระบบตัดซับไตเติลภาษาไทยได้สวยงาม ไม่ขาดกลางคำ"
    )

    if is_edu:
        return f"""คุณเขียนคอนเทนต์ให้ความรู้บนโซเชียลภาษาไทยให้แบรนด์ Sangkan Clean
{THAI_TONE_RULES}
{seo_geo_rules}

หัวข้อวันนี้: {topic["label"]}
มุม: {topic["angle"]}
หัวข้อกราฟิก: {topic["headline"]}

** สำคัญมาก: โพสต์นี้เป็น "คอนเทนต์ให้ความรู้" (Educational Content) **
- เน้นให้ข้อมูลที่มีประโยชน์ น่าสนใจ อ่านสนุก
- ห้ามขายตรง ห้ามใส่ CTA บอกให้ทักไลน์หรือโทร
- ห้ามพูดถึงราคาหรือแพ็คบริการ
- ลงชื่อแบรนด์ท้ายโพสต์เบาๆ เช่น "เกร็ดความรู้จาก Sangkan Clean" หรือ "Sangkan Clean ใส่ใจเรื่องสะอาด"
- โทนคุยเพื่อนทำงาน ไม่เป็นทางการ ให้ข้อมูลเชิง fact
- สร้างบทพูดพากย์ (voiceover_text) สั้นกระชับ ความยาว 45-70 คำ เพื่อใช้อ่านออกเสียงใน Reels ขนาด 15 วินาที

คืน JSON เท่านั้น:
{{
  "fb_ig": "แคปชัน Facebook/Instagram ภาษาไทย 60-140 คำ ให้ความรู้ ไม่ขาย แทรกคีย์เวิร์ด SEO",
  "tiktok": "แคปชัน TikTok สั้น 30-70 คำ ให้ความรู้ ไม่ขาย",
  "line": "ข้อความ LINE broadcast 40-100 คำ ให้ความรู้ ไม่ขาย ห้ามขึ้นต้นด้วย เรียน",
  "image_subline": "ประโยครองใต้หัวข้อบนกราฟิก ภาษาไทย สั้นมาก ไม่เกิน {SUBLINE_MAX} ตัวอักษร",
  "voiceover_text": "บทพากย์วิดีโอ Reels ภาษาไทย ความยาว 45-70 คำ สำหรับพากย์ด้วย AI เสียงนุ่ม น่าเชื่อถือ ห้ามมีวงเล็บ ห้ามมีเครื่องหมายอ่านออกเสียงแปลกๆ",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
}}
"""

    # Promo prompt (original)
    return f"""คุณเขียนคอนเทนต์โซเชียลภาษาไทยให้แบรนด์ Sangkan Clean เท่านั้น
{THAI_TONE_RULES}
{seo_geo_rules}

หัวข้อวันนี้: {topic["label"]}
มุม: {topic["angle"]}
หัวข้อกราฟิก: {topic["headline"]}
CTA ที่ต้องมี: LINE {LINE_OA} และเว็บ {SITE}
โทรศัพท์ (ใส่ได้ถ้าเหมาะสม): {PHONE}

- สร้างบทพูดพากย์ (voiceover_text) สั้นกระชับ ความยาว 45-70 คำ เพื่อใช้อ่านออกเสียงโปรโมตใน Reels ขนาด 15 วินาที

คืน JSON เท่านั้น:
{{
  "fb_ig": "แคปชัน Facebook/Instagram ภาษาไทย 60-140 คำ มี CTA โทนคุยเพื่อนทำงาน แทรกคีย์เวิร์ด SEO",
  "tiktok": "แคปชัน TikTok สั้น 30-70 คำ โทนเดียวกัน",
  "line": "ข้อความ LINE broadcast 40-100 คำ โทนเดียวกัน ห้ามขึ้นต้นด้วย เรียน",
  "image_subline": "ประโยครองใต้หัวข้อบนกราฟิก ภาษาไทย สั้นมาก ไม่เกิน {SUBLINE_MAX} ตัวอักษร",
  "voiceover_text": "บทพากย์โปรโมตวิดีโอ Reels ภาษาไทย ความยาว 45-70 คำ สำหรับพากย์ด้วย AI เสียงเป็นมิตรและกระตุ้นการตัดสินใจ ห้ามมีวงเล็บ ห้ามมีเครื่องหมายอ่านออกเสียงแปลกๆ",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
}}
"""


def _generate_captions(topic: dict) -> tuple[dict, str]:
    """Generate captions. Returns (captions_dict, source_name)."""
    try:
        from gemini_api import call_gemini_json_rotate, get_api_keys, call_openai_json
    except ImportError:
        return _fallback_captions(topic), "fallback"

    all_kws = _load_seo_keywords()
    kws = _pick_seo_keywords(topic, all_kws)
    print(f"SEO/AIO/GEO selected keywords: {kws}")
    prompt = _build_prompt(topic, keywords=kws)
    data = None
    caption_source = "fallback"
    keys = get_api_keys()

    # 1. Gemini
    if keys:
        print(f"Captions: rotating across {len(keys)} Gemini API key(s)")
        data = call_gemini_json_rotate(keys, prompt, key_label_prefix="social-bot")
        if data and isinstance(data, dict):
            caption_source = "gemini"

    # 2. OpenAI
    if not data or not isinstance(data, dict):
        openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if openai_key:
            print("Gemini key missing or failed — trying OpenAI fallback")
            data = call_openai_json(prompt)
            if data and isinstance(data, dict):
                caption_source = "openai"

    # 3. Fallback
    if not data or not isinstance(data, dict):
        print("Both Gemini and OpenAI unavailable/failed — using fallback captions")
        return _fallback_captions(topic), "fallback"

    print(f"Caption source: {caption_source}")
    base = _fallback_captions(topic)
    for key in ("fb_ig", "tiktok", "line", "image_subline", "voiceover_text", "hashtags"):
        if key in data and data[key]:
            base[key] = data[key]
    if isinstance(base.get("image_subline"), str):
        base["image_subline"] = clip_subline(base["image_subline"])
    for key in ("fb_ig", "tiktok", "line", "image_subline"):
        if isinstance(base.get(key), str):
            base[key] = (
                base[key]
                .replace("สั่งการคลีน", "Sangkan Clean")
                .replace("สังการคลีน", "Sangkan Clean")
            )
    return base, caption_source


def _stamp() -> str:
    from datetime import timezone, timedelta
    tz_bangkok = timezone(timedelta(hours=7))
    return datetime.now(tz_bangkok).strftime("%Y%m%d")


# Scene one-liners only — shared Instagram lifestyle brief is in creative_standard.
SCENE_BY_TOPIC: dict[str, str] = {
    # --- Promo topics (original) ---
    "office_ondemand": (
        "open Bangkok coworking floor, young professionals working casually at desks, "
        "floor-to-ceiling windows, indoor plants"
    ),
    "agency_focus": (
        "creative agency studio with soft moodboard wall, tidy open plan, "
        "casual-smart team collaborating in soft focus"
    ),
    "tech_team": (
        "bright startup office with clean desks and monitors, "
        "energetic but uncluttered, glass meeting room soft background"
    ),
    "big_cleaning": (
        "freshly deep-cleaned modern office after hours, polished floors catching daylight, "
        "subtle cleaning tools softly blurred in background"
    ),
    "maid_backup": (
        "bright clean office interior with a discreet professional cleaning cart "
        "softly out of focus — not a stiff utility room"
    ),
    "service_area": (
        "airy Bangkok office interior with soft city light through windows, "
        "clean desks and plants in foreground"
    ),
    "price_pack": (
        "premium small home-office / boutique agency desk lifestyle shot, "
        "notebook plant morning light, left third kept simple"
    ),
    "affiliate": (
        "two young colleagues chatting casually in a café-style office lounge, "
        "friendly daylight, clean modern space"
    ),
    "after_construction": (
        "professional Thai cleaning team in uniforms cleaning paint spots, "
        "dust, and window frames in a newly built modern house in Thailand"
    ),
    "soft_cleaning": (
        "gentle daily tidy of a modern condo living area / soft surfaces, "
        "microfiber cloths subtle, calm natural light"
    ),
    # --- Edu topics ---
    "edu_desk_germ": (
        "close-up of an office desk with keyboard, phone and coffee mug, "
        "subtle microscopic bacteria overlay hint, clean modern office background"
    ),
    "edu_germ_lifespan": (
        "split view of clean vs dirty office desk surface, "
        "subtle glow highlighting germs, modern infographic style"
    ),
    "edu_productivity": (
        "tidy bright office with focused team working, productivity graphs "
        "softly overlaid, morning sunlight through windows"
    ),
    "edu_creative_block": (
        "cluttered messy desk contrasted with clean creative workspace, "
        "lightbulb moment concept, soft warm lighting"
    ),
    "edu_dust_it": (
        "close-up of dusty computer fan and vents, "
        "tech office background softly blurred, dramatic side lighting"
    ),
    "edu_server_room": (
        "clean server room with blinking lights, "
        "pristine cable management, cool blue lighting"
    ),
    "edu_big_clean_why": (
        "before-after split of office deep cleaning, "
        "one side dusty corners, other side spotless, natural daylight"
    ),
    "edu_hidden_dirt": (
        "under-desk view showing hidden dust and debris, "
        "air vent with dust buildup, revealing lighting angle"
    ),
    "edu_checklist": (
        "professional cleaning checklist on clipboard in clean office, "
        "checkmarks visible, organized cleaning supplies nearby"
    ),
    "edu_maid_absent": (
        "empty reception area of small office, slightly untidy, "
        "no cleaning staff visible, morning light"
    ),
    "edu_zone_problems": (
        "Bangkok cityscape with different office zones highlighted, "
        "aerial view showing urban dust and traffic, warm golden hour"
    ),
    "edu_pm25": (
        "office window view of hazy Bangkok skyline, "
        "air purifier in foreground, soft atmospheric lighting"
    ),
    "edu_outsource_vs_hire": (
        "split comparison layout: one side shows HR paperwork pile, "
        "other side shows professional cleaning team, balanced lighting"
    ),
    "edu_hidden_cost": (
        "calculator and expense receipts on office desk, "
        "subtle cost comparison infographic style, clean background"
    ),
    "edu_building_hygiene": (
        "modern office building corridor with multiple office doors, "
        "clean shared spaces, professional lighting"
    ),
    "edu_zone_clean": (
        "open plan office floor with multiple tenant spaces, "
        "clean common area, collaborative atmosphere"
    ),
    "edu_construction_dust": (
        "interior of a modern office space in Bangkok post-renovation, "
        "thin layer of concrete dust on a desk, a hand wipe revealing clean wood beneath, "
        "safety warning mood"
    ),
    "edu_move_in_clean": (
        "newly renovated empty office floor in a Bangkok building, "
        "window glass sparkling clean, Thai cleaners vacuuming and detailing final spots "
        "before tenant move-in"
    ),
    "edu_routine_clean": (
        "calendar with cleaning schedule marked, modern office desk, "
        "organized routine concept, soft morning light"
    ),
    "edu_harsh_chemical": (
        "damaged office furniture surface from wrong cleaning product, "
        "peeling leather or stained wood, cautionary close-up"
    ),
}


def _background_prompt(topic: dict) -> str:
    scene = SCENE_BY_TOPIC.get(topic["id"], "")
    return build_background_prompt(
        scene,
        topic_mood=str(topic.get("label", topic["id"])),
    )


# Same lifestyle photo pool as blog covers (Pillow overlay) — not genz/art ads.
STOCK_BG_DIR = REPO / "images" / "blog" / "bg"
VENUE_BY_TOPIC: dict[str, str] = {
    # Promo
    "office_ondemand": "office",
    "agency_focus": "office",
    "tech_team": "office",
    "big_cleaning": "office",
    "maid_backup": "office",
    "service_area": "office",
    "price_pack": "office",
    "affiliate": "office",
    "after_construction": "warehouse",
    "soft_cleaning": "home",
    # Edu — inherit from their cluster's promo venue
    "edu_desk_germ": "office",
    "edu_germ_lifespan": "office",
    "edu_productivity": "office",
    "edu_creative_block": "office",
    "edu_dust_it": "office",
    "edu_server_room": "office",
    "edu_big_clean_why": "office",
    "edu_hidden_dirt": "office",
    "edu_checklist": "office",
    "edu_maid_absent": "office",
    "edu_zone_problems": "office",
    "edu_pm25": "office",
    "edu_outsource_vs_hire": "office",
    "edu_hidden_cost": "office",
    "edu_building_hygiene": "office",
    "edu_zone_clean": "office",
    "edu_construction_dust": "warehouse",
    "edu_move_in_clean": "warehouse",
    "edu_routine_clean": "office",
    "edu_harsh_chemical": "office",
}

# Keyword → venue (same idea as compose_blog_covers.venue_of). First match wins.
VENUE_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("โรงงาน",), "factory"),
    (("โกดัง",), "warehouse"),
    (("โรงแรม", "รีสอร์ท"), "hotel"),
    (("โรงพยาบาล", "คลินิก"), "hospital"),
    (("โรงเรียน", "มหาวิทยาลัย"), "school"),
    (("ห้าง", "ศูนย์การค้า"), "mall"),
    (("ร้านอาหาร", "คาเฟ่"), "restaurant"),
    (("โชว์รูม",), "showroom"),
    (("ตึกสูง",), "highrise"),
    (("ฟิตเนส",), "gym"),
    (("คอนโด", "บ้าน", "โฮม"), "home"),
    (("ออฟฟิศ", "สำนักงาน", "อาคาร", "เอเจนซี่", "สตาร์ทอัพ", "tech"), "office"),
    (("ก่อสร้าง", "ฝุ่นปูน", "คราบสี"), "warehouse"),
]

VENUE_FALLBACK: dict[str, list[str]] = {
    "school": ["office", "home"],
    "mall": ["showroom", "office"],
    "hospital": ["office"],
    "restaurant": ["mall", "office"],
    "home": ["highrise", "office"],
    "hotel": ["home", "office"],
    "warehouse": ["factory", "office"],
    "factory": ["warehouse", "office"],
    "showroom": ["mall", "office"],
    "highrise": ["office", "home"],
    "gym": ["office"],
    "office": ["home"],
}


def _bg_venue(path: Path) -> str:
    m = re.match(r"bg-([a-z]+)-\d+", path.stem)
    return m.group(1) if m else ""


def _venue_from_text(text: str) -> str | None:
    blob = (text or "").lower()
    for keys, venue in VENUE_KEYWORDS:
        if any(k.lower() in blob for k in keys):
            return venue
    return None


def _expected_venue(topic: dict, captions: dict | None = None) -> str:
    """Infer venue from copy first, then topic default — so bg matches the post."""
    parts = [
        str(topic.get("headline", "")),
        str(topic.get("angle", "")),
        str(topic.get("label", "")),
    ]
    if captions:
        for key in ("fb_ig", "image_subline", "tiktok", "line"):
            if captions.get(key):
                parts.append(str(captions[key]))
    hit = _venue_from_text(" ".join(parts))
    if hit:
        return hit
    return VENUE_BY_TOPIC.get(topic["id"], "office")


def _venue_ok(need: str, got: str) -> bool:
    if not got:
        return False
    if need == got:
        return True
    return got in VENUE_FALLBACK.get(need, [])


def _list_stock_bgs(venue: str) -> list[Path]:
    """Numbered venue files only: bg-{venue}-NN.jpg (same rule as blog covers)."""
    if not STOCK_BG_DIR.is_dir():
        return []
    files = sorted(STOCK_BG_DIR.glob(f"bg-{venue}-*.jpg"))
    files += sorted(STOCK_BG_DIR.glob(f"bg-{venue}-*.png"))
    return files


def _stock_background(topic: dict, venue: str | None = None) -> Path | None:
    """Pick a lifestyle photo matching the expected venue (+ related fallbacks)."""
    need = venue or _expected_venue(topic)
    order = [need] + [v for v in VENUE_FALLBACK.get(need, []) if v != need]
    pool: list[Path] = []
    for v in order:
        pool = _list_stock_bgs(v)
        if pool:
            need = v
            break
    if not pool:
        pool = _list_stock_bgs("office")
        need = "office"
    if not pool:
        return None
    seed = f"{_stamp()}:{topic['id']}:{need}"
    idx = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16) % len(pool)
    chosen = pool[idx]
    print(f"Stock venue need={need} file={chosen.name}")
    return chosen


def _gemini_background(topic: dict, out_dir: Path) -> Path | None:
    """Optional Gemini image gen (often 429 on free tier)."""
    try:
        from gemini_api import call_gemini_image_rotate, get_api_keys
    except ImportError:
        return None

    keys = get_api_keys()
    if not keys:
        return None

    print(f"Background: trying Gemini across {len(keys)} key(s)")
    raw = call_gemini_image_rotate(
        keys, _background_prompt(topic), key_label_prefix="social-bot-bg"
    )
    if not raw:
        return None

    ext = "png" if raw[:8].startswith(b"\x89PNG") else "jpg"
    path = out_dir / f"bg.{ext}"
    path.write_bytes(raw)
    print(f"Gemini background saved -> {path.name} ({len(raw)} bytes)")
    return path


def _resolve_background(
    topic: dict,
    out_dir: Path,
    captions: dict | None = None,
    force_venue: str | None = None,
) -> tuple[Path | None, dict]:
    """Return (bg_path, meta) with venue relevance fields."""
    need = force_venue or _expected_venue(topic, captions)
    meta = {
        "venue_need": need,
        "venue_got": "",
        "bg_source": "",
        "relevance_ok": False,
    }

    topic_type = topic.get("type", "promo")
    use_gemini_bg = _env_bool("SOCIAL_GEMINI_BG", default=False) or (topic_type == "edu")

    if use_gemini_bg and not force_venue:
        gem = _gemini_background(topic, out_dir)
        if gem:
            # Gemini has no venue tag — treat as ok but mark source
            meta.update(
                {
                    "venue_got": "gemini",
                    "bg_source": gem.name,
                    "relevance_ok": True,
                }
            )
            return gem, meta
        print("Gemini bg unavailable — falling back to stock lifestyle photo")

    stock = _stock_background(topic, venue=need)
    if stock and stock.exists():
        got = _bg_venue(stock) or need
        ok = _venue_ok(need, got)
        dest = out_dir / f"bg{stock.suffix.lower()}"
        shutil.copy2(stock, dest)
        meta.update(
            {
                "venue_got": got,
                "bg_source": stock.name,
                "relevance_ok": ok,
            }
        )
        print(
            f"Stock lifestyle bg -> {stock.name} "
            f"(need={need} got={got} ok={ok})"
        )
        if not ok:
            print(f"RELEVANCE WARN: bg {stock.name} does not match venue {need}")
        return dest, meta

    print("No stock bg found — gradient fallback")
    return None, meta


def build_assets(
    topic: dict,
    captions: dict,
    *,
    force_venue: str | None = None,
) -> dict[str, str]:
    """Create PNG (+ MP4 as needed). Returns relative paths under social-bot/."""
    day = _stamp()
    out = OUT_DIR / day
    out.mkdir(parents=True, exist_ok=True)

    headline = topic["headline"]
    sub = clip_subline(str(captions.get("image_subline") or topic["angle"]))

    bg_path, bg_meta = _resolve_background(
        topic, out, captions=captions, force_venue=force_venue
    )

    feed_png = out / "feed.png"
    stories_png = out / "stories.png"
    save_feed(headline, sub, feed_png, topic_id=topic["id"], background=bg_path)
    save_stories(headline, sub, stories_png, topic_id=topic["id"], background=bg_path)

    assets: dict[str, str] = {
        "feed_png": str(feed_png.relative_to(ROOT)).replace("\\", "/"),
        "stories_png": str(stories_png.relative_to(ROOT)).replace("\\", "/"),
        "venue_need": bg_meta.get("venue_need", ""),
        "venue_got": bg_meta.get("venue_got", ""),
        "bg_source": bg_meta.get("bg_source", ""),
        "relevance_ok": "1" if bg_meta.get("relevance_ok") else "0",
    }
    if bg_path and bg_path.exists():
        assets["bg"] = str(bg_path.relative_to(ROOT)).replace("\\", "/")

    disable_video = _env_bool("DISABLE_VIDEO", default=True)
    topic_type = topic.get("type", "promo")
    fmt = "image" if disable_video else ("video" if topic_type == "edu" else topic.get("format", "image"))
    need_stories_video = not disable_video
    need_feed_video = (not disable_video) and (fmt == "video")

    if (need_stories_video or need_feed_video) and not has_ffmpeg():
        print("WARNING: ffmpeg not found — skipping video render")
        return assets

    # Synthesize TTS voiceover & SRT if voiceover script is generated
    audio_path = out / "voiceover.mp3"
    srt_path = out / "stories.srt"
    has_tts = False
    duration = 10.0

    if "voiceover_text" in captions and captions["voiceover_text"]:
        from tts_generator import generate_tts_and_srt, get_srt_duration
        has_tts = generate_tts_and_srt(captions["voiceover_text"], audio_path, srt_path)
        if has_tts:
            duration = get_srt_duration(srt_path, default=10.0)
            assets["voiceover_mp3"] = str(audio_path.relative_to(ROOT)).replace("\\", "/")
            assets["stories_srt"] = str(srt_path.relative_to(ROOT)).replace("\\", "/")

    if need_stories_video:
        stories_mp4 = out / "stories.mp4"
        if has_tts:
            from render_video import render_reels_video_with_audio_and_subs
            render_reels_video_with_audio_and_subs(
                png_path=stories_png,
                audio_path=audio_path,
                srt_path=srt_path,
                mp4_path=stories_mp4,
                duration=duration,
            )
        else:
            render_stories_clip(stories_png, stories_mp4, duration=10.0)
        assets["stories_mp4"] = str(stories_mp4.relative_to(ROOT)).replace("\\", "/")

    if need_feed_video:
        feed_mp4 = out / "feed.mp4"
        if has_tts:
            # Render square video with audio track
            temp_feed_mp4 = out / "feed_silent.mp4"
            render_feed_clip(feed_png, temp_feed_mp4, duration=duration)
            import subprocess
            from render_video import ffmpeg_bin
            cmd = [
                ffmpeg_bin(),
                "-y",
                "-i", str(temp_feed_mp4),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                str(feed_mp4),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            if temp_feed_mp4.exists():
                temp_feed_mp4.unlink()
        else:
            render_feed_clip(feed_png, feed_mp4, duration=10.0)
        assets["feed_mp4"] = str(feed_mp4.relative_to(ROOT)).replace("\\", "/")

    return assets


def _ensure_bg_relevance(topic: dict, captions: dict, assets: dict[str, str]) -> dict[str, str]:
    """Before publish: if stock venue mismatches copy, rebuild with correct venue."""
    need = _expected_venue(topic, captions)
    got = str(assets.get("venue_got") or "")
    if assets.get("relevance_ok") == "1" and _venue_ok(need, got):
        print(f"Relevance OK: venue={got} (need={need})")
        return assets

    if got == "gemini":
        return assets

    print(f"Relevance check FAIL: need={need} got={got or 'none'} — rebuilding assets")
    rebuilt = build_assets(topic, captions, force_venue=need)
    if rebuilt.get("relevance_ok") != "1":
        # Last attempt: office is safest for most social topics
        if need != "office":
            print("Retry relevance with office venue")
            rebuilt = build_assets(topic, captions, force_venue="office")
    return rebuilt


def publish_all(
    topic: dict,
    captions: dict,
    assets: dict[str, str],
    channels: set[str],
    dry_run: bool,
) -> dict[str, dict]:
    disable_video = _env_bool("DISABLE_VIDEO", default=True)
    fmt = "image" if disable_video else ("video" if topic.get("type", "promo") == "edu" else topic.get("format", "image"))
    tags = captions.get("hashtags") or []
    tag_str = " ".join(tags) if isinstance(tags, list) else str(tags)

    fb_caption = f"{captions['fb_ig']}\n\n{tag_str}".strip()
    tt_caption = f"{captions['tiktok']}\n\n{tag_str}".strip()

    def abs_asset(key: str) -> Path | None:
        rel = assets.get(key)
        if not rel:
            return None
        return ROOT / rel

    if "facebook" in channels:
        from publish_meta import publish_facebook

        results["facebook"] = publish_facebook(
            caption=fb_caption,
            image_path=abs_asset("feed_png"),
            video_path=abs_asset("stories_mp4") if fmt == "video" else None,
            use_reels=fmt == "video",
            dry_run=dry_run,
        )

    if "instagram" in channels:
        from publish_meta import publish_instagram

        results["instagram"] = publish_instagram(
            caption=fb_caption,
            image_path=abs_asset("feed_png"),
            video_path=abs_asset("stories_mp4") if fmt == "video" else None,
            use_reels=fmt == "video",
            dry_run=dry_run,
        )

    if "tiktok" in channels:
        from publish_tiktok import publish_tiktok

        results["tiktok"] = publish_tiktok(
            caption=tt_caption,
            video_path=abs_asset("stories_mp4"),
            dry_run=dry_run,
        )

    if "line" in channels:
        from publish_line import publish_line

        results["line"] = publish_line(
            text=captions["line"],
            image_path=abs_asset("feed_png"),
            headline=topic["headline"],
            dry_run=dry_run,
        )

    return results


def main() -> int:
    dry_run = _env_bool("DRY_RUN", default=False)
    channels = _channels()
    log = _load_log()
    topic = pick_topic(log.get("last_topic"))
    topic_type = topic.get("type", "promo")
    disable_video = _env_bool("DISABLE_VIDEO", default=True)
    fmt = "image" if disable_video else ("video" if topic_type == "edu" else topic.get("format", "image"))

    print(f"Topic: {topic['id']} ({fmt}) type={topic_type} dry_run={dry_run} channels={sorted(channels)}")

    captions, caption_source = _generate_captions(topic)
    assets = build_assets(topic, captions)
    assets = _ensure_bg_relevance(topic, captions, assets)
    print("Assets:", json.dumps(assets, ensure_ascii=False))

    if assets.get("relevance_ok") != "1" and assets.get("venue_got") != "gemini":
        print(
            "ABORT publish: image venue does not match post copy "
            f"(need={assets.get('venue_need')} got={assets.get('venue_got')} "
            f"source={assets.get('bg_source')})"
        )
        # Still write log for debugging, but do not publish.
        from datetime import timezone, timedelta
        tz_bangkok = timezone(timedelta(hours=7))
        entry = {
            "ts": datetime.now(tz_bangkok).isoformat(),
            "topic_id": topic["id"],
            "type": topic_type,
            "caption_source": caption_source,
            "format": fmt,
            "dry_run": dry_run,
            "assets": assets,
            "captions": {
                "fb_ig": captions.get("fb_ig", "")[:200],
                "tiktok": captions.get("tiktok", "")[:120],
                "line": captions.get("line", "")[:120],
            },
            "results": {"skipped": {"ok": False, "reason": "bg_relevance"}},
        }
        posts = log.get("posts") or []
        posts.append(entry)
        log["posts"] = posts[-60:]
        log["last_topic"] = topic["id"]
        _save_log(log)
        return 1

    results = publish_all(topic, captions, assets, channels, dry_run)

    from datetime import timezone, timedelta
    tz_bangkok = timezone(timedelta(hours=7))
    entry = {
        "ts": datetime.now(tz_bangkok).isoformat(),
        "topic_id": topic["id"],
        "type": topic_type,
        "caption_source": caption_source,
        "format": fmt,
        "dry_run": dry_run,
        "assets": assets,
        "captions": {
            "fb_ig": captions.get("fb_ig", "")[:200],
            "tiktok": captions.get("tiktok", "")[:120],
            "line": captions.get("line", "")[:120],
        },
        "results": results,
    }
    posts = log.get("posts") or []
    posts.append(entry)
    log["posts"] = posts[-60:]  # keep last ~2 months
    log["last_topic"] = topic["id"]
    _save_log(log)

    # Also dump full captions for dry-run review
    if dry_run:
        day = _stamp()
        cap_path = OUT_DIR / day / "captions.json"
        cap_path.write_text(
            json.dumps(captions, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {cap_path}")

    print("Results:", json.dumps(results, ensure_ascii=False))
    failed = [
        name
        for name, res in results.items()
        if not res.get("ok") and not dry_run and res.get("skipped") is not True
    ]
    if failed:
        print("Publish failures:", failed)
        for name in failed:
            print(f"  {name}: {json.dumps(results.get(name), ensure_ascii=False)}")
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
