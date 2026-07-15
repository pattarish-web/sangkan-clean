"""Daily multi-category GEO blog generator with cover images."""

from __future__ import annotations

import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from build_blogs import slugify
from creative_standard import THAI_TONE_RULES, build_blog_cover_prompt
from gemini_api import (
    call_gemini_image_rotate,
    call_gemini_json_rotate,
    call_openai_json,
    get_api_keys,
    is_key_exhausted,
)
from site_config import SITE_URL

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "posts.json"
IMAGES_DIR = ROOT / "blog" / "images"
STOCK_DIR = ROOT / "images" / "blog"

POSTS_PER_CATEGORY = max(1, int(os.environ.get("POSTS_PER_CATEGORY", "1")))
# Soft pause between posts (per-key throttle also applies in gemini_api).
POST_GAP_SEC = float(os.environ.get("BLOG_POST_GAP_SEC", "5"))
EXPECTED_DAILY = POSTS_PER_CATEGORY * 3  # เคล็ดลับ / ธุรกิจ / คู่มือ — ไม่รวมบริการ

TOPICS = [
    {
        "category": "เคล็ดลับ",
        "keywords": [
            "ทำความสะอาดบ้าน",
            "ขจัดคราบห้องน้ำ",
            "วิธีกำจัดไรฝุ่น",
            "ขจัดคราบฝังลึก",
            "ล้างกระจกให้ใส",
            "ทำความสะอาดครัวมันเยิ้ม",
            "กำจัดกลิ่นอับในบ้าน",
            "เช็ดพื้นไม้ไม่ให้เสีย",
            "ทำความสะอาดโซฟาผ้า",
            "วิธีซักพรมด้วยตัวเอง",
            "ลดฝุ่น PM2.5 ในบ้าน",
            "ทำความสะอาดเครื่องปรับอากาศเบื้องต้น",
            "ขจัดคราบน้ำมันกระทะ",
            "จัดเก็บของให้บ้านดูโปร่ง",
            "ทำความสะอาดระเบียงคอนโด",
            "เคล็ดลับถูพื้นไม้มะเดื่อไม่เป็นคราบ",
            "วิธีซักม่านคอนโดเองอย่างปลอดภัย",
            "กำจัดเชื้อราในห้องน้ำแบบยั่งยืน",
            "จัดห้องทำงานที่บ้านให้น้อยฝุ่น",
            "ดูแลกระเบื้องยาแนวไม่ให้ดำ",
        ],
    },
    {
        "category": "ธุรกิจ",
        "keywords": [
            "จัดหาแม่บ้านประจำ",
            "บริษัททำความสะอาด ออฟฟิศ",
            "แม่บ้านสำนักงาน ดีอย่างไร",
            "Big Cleaning โรงงาน",
            "แม่บ้านคอนโด",
            "จ้างบริษัททำความสะอาด vs แม่บ้านรายวัน",
            "มาตรฐาน QC บริการทำความสะอาด",
            "ค่าบริการแม่บ้านประจำสำนักงาน",
            "เลือกผู้รับเหมา Big Cleaning",
            "ทำความสะอาดคลินิกมาตรฐานสุขอนามัย",
            "แม่บ้านโรงแรม outsource",
            "สัญญาบริการทำความสะอาดรายเดือน",
            "ลดต้นทุนทำความสะอาดออฟฟิศ",
            "ทีมสำรองแม่บ้านสำคัญอย่างไร",
            "บริการทำความสะอาด B2B",
            "KPI ทีมแม่บ้านออฟฟิศที่วัดได้",
            "แม่บ้าน coworking สำหรับสตาร์ทอัพ",
            "เปรียบเทียบแพ็คแม่บ้านรายเดือน",
            "outsourcing คลีนโรงงาน vs in-house",
            "รายงานก่อน–หลังงานคลีนสำหรับผู้บริหาร",
        ],
    },
    {
        "category": "คู่มือ",
        "keywords": [
            "เช็คลิสต์ก่อนเลือกแม่บ้าน",
            "มาตรฐานบริการทำความสะอาด",
            "น้ำยาทำความสะอาดที่ปลอดภัย",
            "ทำความสะอาดหลังก่อสร้าง",
            "เตรียมบ้านก่อนทีม Big Cleaning เข้างาน",
            "เปรียบเทียบ Soft Cleaning กับ Big Cleaning",
            "เช็คลิสต์ตรวจรับงานทำความสะอาด",
            "เลือกน้ำยา eco-friendly",
            "ความปลอดภัยแม่บ้านในออฟฟิศ",
            "แผนทำความสะอาดรายสัปดาห์สำนักงาน",
            "คู่มือจองคิวบริการทำความสะอาด",
            "เอกสารที่ควรขอจากบริษัทแม่บ้าน",
            "วิธีประเมินราคาทำความสะอาดเบื้องต้น",
            "ดูแลพื้นผิวหินอ่อนหลังขัด",
            "คู่มืออบโอโซนก่อนเข้าอยู่",
            "เช็คลิสต์ตรวจพื้นที่ก่อนเปิดออฟฟิศใหม่",
            "ขั้นตอนรับมอบงานหลัง Big Cleaning",
            "คู่มือเตรียมห้องประชุมก่อนอีเวนต์",
            "ตรวจรับงานคลีนคลินิกอย่างปลอดภัย",
            "แผนคลีนรายเดือนสำหรับโฮมออฟฟิศ",
        ],
    },
]

# Keyword fragment → stock cover under images/blog/
# Office/B2B before home so "แม่บ้านออฟฟิศ" does not match "บ้าน" inside "แม่บ้าน".
_STOCK_RULES: list[tuple[tuple[str, ...], str]] = [
    (("โรงงาน",), "blog-factory.jpg"),
    (("โกดัง",), "blog-warehouse.jpg"),
    (("โรงแรม", "รีสอร์ท"), "blog-hotel.jpg"),
    (("โรงพยาบาล", "คลินิก"), "blog-hospital.jpg"),
    (("โรงเรียน", "มหาวิทยาลัย"), "blog-school.jpg"),
    (("ห้าง", "ศูนย์การค้า"), "blog-mall.jpg"),
    (("ร้านอาหาร", "คาเฟ่", "ครัว"), "blog-restaurant.jpg"),
    (("โชว์รูม",), "blog-showroom.jpg"),
    (("ตึกสูง", "กระจก"), "blog-highrise.jpg"),
    (("ฟิตเนส",), "blog-gym.jpg"),
    (("ออฟฟิศ", "สำนักงาน", "อาคาร", "cowork", "b2b"), "blog-office.jpg"),
    (("คอนโด", "โซฟา", "พรม", "ระเบียง", "ม่าน", "ในบ้าน", "ที่บ้าน"), "blog-home.jpg"),
]

_CATEGORY_STOCK = {
    "เคล็ดลับ": "blog-home.jpg",
    "ธุรกิจ": "blog-office.jpg",
    "คู่มือ": "blog-office.jpg",
}


def _pick_key(api_keys: list[str], offset: int) -> str | None:
    if not api_keys:
        return None
    for i in range(len(api_keys)):
        key = api_keys[(offset + i) % len(api_keys)]
        if not is_key_exhausted(key):
            return key
    return None


def _geo_prompt(keyword: str, category: str) -> str:
    return f"""คุณเป็นผู้เชี่ยวชาญด้านการทำความสะอาดและนักเขียนบทความ SEO/GEO (Generative Engine Optimization)
ช่วยเขียนบทความบล็อกภาษาไทยแบบเจาะลึกเกี่ยวกับหัวข้อ: "{keyword}"
หมวด: {category}
แบรนด์อ้างอิงได้: Sangkan Clean (ไม่ต้องใส่ชื่อแบรนด์ใน title)

{THAI_TONE_RULES}

ข้อกำหนด (สำคัญมากสำหรับการทำ GEO เพื่อให้ AI นำไปอ้างอิง):
1. title: น่าสนใจ ดึงดูดคลิก มีคำค้นหาหลัก ความยาวไม่เกิน 100 ตัวอักษร — ห้ามต่อท้ายด้วย "– Sangkan Clean"
2. description: สรุปสั้นๆ 100-160 ตัวอักษร
3. content: โค้ด HTML semantic ล้วนๆ (ไม่มี <html> <body>) บังคับโครงนี้:
   - <h2>สรุปประเด็นสำคัญ (Key Takeaways)</h2> ตามด้วย <ul><li> 3-4 ข้อ
   - <h2>เนื้อหาหลัก</h2> อธิบายเจาะลึก มี <strong> เน้นคำสำคัญ
   - <h2>ข้อมูลสถิติที่น่าสนใจ</h2> ใช้ตัวเลขแนวโน้มอุตสาหกรรมโดยประมาณ พร้อมระบุว่าเป็นข้อมูลโดยประมาณ
   - <h2>คำถามที่พบบ่อย (FAQ)</h2> ถามตอบ 2-3 ข้อสั้นๆ

ตอบเป็น JSON เท่านั้น:
{{"title":"...","description":"...","content":"<h2>สรุปประเด็นสำคัญ...</h2>..."}}"""


def _image_prompt(title: str, keyword: str, category: str) -> str:
    scene_hints = {
        "เคล็ดลับ": (
            "bright Bangkok condo living room after tidy-up, young SEA professional "
            "in casual-smart clothes near indoor plants, airy lifestyle mood"
        ),
        "ธุรกิจ": (
            "modern Bangkok coworking office, young East/SEA creative team, "
            "clean desks, teal and coral accent props, energetic Gen-Z agency vibe"
        ),
        "คู่มือ": (
            "young SEA professional reviewing a cleaning checklist on a tablet "
            "in a bright Bangkok home-office, shallow depth of field"
        ),
    }
    scene = scene_hints.get(category, "")
    return build_blog_cover_prompt(
        scene,
        topic_mood=category,
        extra=f"Keyword: {keyword}. Title context: {title}.",
    )


def _stock_cover_filename(keyword: str, category: str) -> str:
    # Neutralize "แม่บ้าน" so fragment "บ้าน" / home cues do not false-match.
    hay = f"{keyword} {category}".replace("แม่บ้าน", "MAID").lower()
    for fragments, filename in _STOCK_RULES:
        if any(frag.lower() in hay for frag in fragments):
            return filename
    return _CATEGORY_STOCK.get(category, "blog-office.jpg")


def _get_bg_prefix(keyword: str, category: str) -> str:
    stock_file = _stock_cover_filename(keyword, category)
    base = stock_file.replace("blog-", "").replace(".jpg", "")
    return f"bg-{base}-"


def call_openai_image(prompt: str) -> bytes | None:
    """Generate cover image via DALL-E 3 and download the raw bytes."""
    import os
    import requests
    from gemini_api import log
    
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        log("call_openai_image: No OPENAI_API_KEY found", level="WARN")
        return None
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "url",
    }
    url = "https://api.openai.com/v1/images/generations"
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            log(f"OpenAI Image API error {response.status_code}: {response.text[:200]}", level="WARN")
            return None
        data = response.json()
        img_url = data["data"][0]["url"]
        log("OpenAI DALL-E 3 → success, downloading image...")
        img_res = requests.get(img_url, timeout=60)
        if img_res.status_code == 200:
            return img_res.content
        log(f"Failed to download OpenAI image from URL: {img_res.status_code}", level="WARN")
    except Exception as exc:
        log(f"call_openai_image error: {exc}", level="ERROR")
    return None


def _call_openai_multimodal_select(
    title: str,
    keyword: str,
    candidates_with_data: list[tuple[str, bytes]],
) -> str | None:
    import base64
    import json
    import os
    import requests
    from gemini_api import log
    
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        log("_call_openai_multimodal_select: No OPENAI_API_KEY found", level="WARN")
        return None
        
    content_parts = [
        {
            "type": "text",
            "text": (
                "You are Sangkan Clean's Creative Director. Select the single best-matching background image "
                f"for a blog post.\nTitle: {title}\nKeyword: {keyword}\n\n"
                "Analyze all candidate images below and select the one that visually matches the blog's topic the best. "
                "Respond in JSON format: {\"best_image\": \"<filename>\"}"
            )
        }
    ]
    for filename, img_bytes in candidates_with_data:
        content_parts.append({"type": "text", "text": f"Candidate image: {filename}"})
        mime_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
        base64_data = base64.b64encode(img_bytes).decode("utf-8")
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_data}"
            }
        })
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": content_parts}],
        "response_format": {"type": "json_object"},
    }
    url = "https://api.openai.com/v1/chat/completions"
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            log(f"OpenAI Multimodal API error {response.status_code}: {response.text[:200]}", level="WARN")
            return None
        data = response.json()
        text_response = data["choices"][0]["message"]["content"]
        result = json.loads(text_response)
        return result.get("best_image")
    except Exception as exc:
        log(f"_call_openai_multimodal_select error: {exc}", level="ERROR")
    return None


def _fallback_image_url(
    keyword: str,
    category: str,
    title: str = "",
) -> str:
    bg_dir = STOCK_DIR / "bg"
    if bg_dir.exists() and title and os.environ.get("OPENAI_API_KEY"):
        prefix = _get_bg_prefix(keyword, category)
        candidates = sorted([
            f.name for f in bg_dir.iterdir()
            if f.name.startswith(prefix) and f.suffix.lower() in (".jpg", ".jpeg", ".png")
        ])
        if candidates:
            candidates_with_data = []
            for name in candidates[:8]:
                try:
                    p = bg_dir / name
                    candidates_with_data.append((name, p.read_bytes()))
                except Exception:
                    pass
            if candidates_with_data:
                print(f"  multimodal selection from {len(candidates_with_data)} candidates for '{title}'")
                best_image = _call_openai_multimodal_select(title, keyword, candidates_with_data)
                if best_image:
                    clean_name = os.path.basename(best_image)
                    target_path = bg_dir / clean_name
                    if target_path.exists():
                        print(f"  multimodal selected → {clean_name}")
                        return f"{SITE_URL}/images/blog/bg/{clean_name}"

    # Default fallback
    filename = _stock_cover_filename(keyword, category)
    path = STOCK_DIR / filename
    if path.exists():
        return f"{SITE_URL}/images/blog/{filename}"
    return f"{SITE_URL}/og-image.png"


def _save_cover(
    api_keys: list[str],
    slug: str,
    title: str,
    keyword: str,
    category: str,
) -> str:
    """Generate cover via OpenAI DALL-E 3 before stock fallback."""
    prompt = _image_prompt(title, keyword, category)
    print("  cover: generating via OpenAI DALL-E 3")
    raw = call_openai_image(prompt)
    if not raw:
        url = _fallback_image_url(keyword, category, title)
        print(f"  cover fallback → {url.split('/')[-1]} ({slug})")
        return url

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ext = "png" if raw[:8].startswith(b"\x89PNG") else "jpg"
    filename = f"{slug}.{ext}"
    path = IMAGES_DIR / filename
    path.write_bytes(raw)
    url = f"{SITE_URL}/blog/images/{filename}"
    print(f"  cover saved → blog/images/{filename} ({len(raw)} bytes)")
    return url


def generate_one_post(
    api_keys: list[str],
    category: str,
    keyword: str,
    key_offset: int,
    existing_titles: set[str],
    existing_slugs: set[str],
):
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not openai_key and (not api_keys or all(is_key_exhausted(k) for k in api_keys)):
        print("All API keys exhausted — stop generating.")
        return None, "quota"

    if openai_key:
        print(f"[{category}] {keyword} via OpenAI GPT-4o-mini")
        result = call_openai_json(
            _geo_prompt(keyword, category),
            timeout=90,
        )
    else:
        start = _pick_key(api_keys, key_offset)
        ordered = api_keys
        if start and start in api_keys:
            i = api_keys.index(start)
            ordered = api_keys[i:] + api_keys[:i]

        print(f"[{category}] {keyword} via {len(ordered)} key(s)")
        result = call_gemini_json_rotate(
            ordered,
            _geo_prompt(keyword, category),
            key_label_prefix="blog",
            timeout=90,
        )
        
    if not result:
        if not openai_key and all(is_key_exhausted(k) for k in api_keys):
            return None, "quota"
        return None, "fail"

    title = (result.get("title") or "").strip()
    description = (result.get("description") or "").strip()
    content = result.get("content") or ""

    if not title or not description:
        print("  invalid JSON fields — skip")
        return None, "fail"
    if "สรุปประเด็นสำคัญ" not in content:
        print("  missing GEO marker — skip")
        return None, "fail"
    if title in existing_titles:
        print(f"  duplicate title — skip: {title[:60]}")
        return None, "dup"

    slug = slugify(title) or f"post-{int(time.time())}"
    if slug in existing_slugs:
        print(f"  duplicate slug — skip: {slug[:60]}")
        return None, "dup"

    image_url = _save_cover(ordered, slug, title, keyword, category)

    today = datetime.today().strftime("%Y-%m-%d")
    post = {
        "title": title,
        "description": description,
        "content": content,
        "category": category,
        "image": image_url,
        "date": today,
        "dateModified": today,
        "slug": slug,
        "geo_source": "openai" if openai_key else "gemini",
    }
    print(f"  OK: {title[:70]}")
    return post, "ok"


def run_daily_batch() -> int:
    api_keys = get_api_keys()
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_keys and not openai_key:
        print("Error: Neither GEMINI_API_KEY nor OPENAI_API_KEY environment variable found.")
        return 0

    if JSON_PATH.exists():
        with open(JSON_PATH, encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []

    existing_titles = {p.get("title") for p in posts if p.get("title")}
    existing_slugs = {p.get("slug") for p in posts if p.get("slug")}
    used_keywords: set[str] = set()
    added = 0
    key_offset = 0

    print(
        f"Daily GEO blogs: {POSTS_PER_CATEGORY}/category × {len(TOPICS)} categories "
        f"(expected={EXPECTED_DAILY}, exclude บริการ) | keys={len(api_keys)}"
    )

    for topic in TOPICS:
        category = topic["category"]
        keywords = list(topic["keywords"])
        random.shuffle(keywords)
        made = 0
        for keyword in keywords:
            if made >= POSTS_PER_CATEGORY:
                break
            if keyword in used_keywords:
                continue
            used_keywords.add(keyword)

            post, status = generate_one_post(
                api_keys,
                category,
                keyword,
                key_offset,
                existing_titles,
                existing_slugs,
            )
            key_offset += 1

            if status == "quota":
                print("Stopping early due to quota.")
                _write_posts(posts)
                return added
            if status != "ok" or not post:
                # Retry next keyword in this category until quota filled.
                continue

            posts.append(post)
            existing_titles.add(post["title"])
            existing_slugs.add(post["slug"])
            added += 1
            made += 1
            if POST_GAP_SEC > 0:
                time.sleep(POST_GAP_SEC)

        print(f"Category {category}: +{made}/{POSTS_PER_CATEGORY}")

    _write_posts(posts)
    print(f"Added {added} posts total (target {EXPECTED_DAILY}).")
    return added


def _write_posts(posts: list) -> None:
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def _rebuild_site() -> None:
    import build_blogs
    import build_listings
    import update_sitemap

    build_blogs.build_blogs()
    build_listings.build_listings()
    update_sitemap.update_sitemap()
    print("Rebuild blogs + listings + sitemap done.")


def main() -> int:
    added = run_daily_batch()
    if added <= 0:
        print("No new posts — skip rebuild.")
        print(f"FAIL: expected {EXPECTED_DAILY} new posts, got 0")
        return 1

    try:
        _rebuild_site()
    except Exception as exc:
        print(f"Error building static blogs/listings/sitemap: {exc}")
        return 1

    if added < EXPECTED_DAILY:
        print(f"FAIL: under-delivery — got {added}/{EXPECTED_DAILY}")
        return 1

    print(f"OK: daily target met ({added}/{EXPECTED_DAILY})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
