"""Daily multi-category GEO blog generator with cover images."""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path

from build_blogs import slugify
from gemini_api import (
    call_gemini_image,
    call_gemini_json,
    get_api_keys,
    is_key_exhausted,
)
from site_config import SITE_URL

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "posts.json"
IMAGES_DIR = ROOT / "blog" / "images"

POSTS_PER_CATEGORY = max(1, int(os.environ.get("POSTS_PER_CATEGORY", "2")))
# Soft pause between posts (per-key throttle also applies in gemini_api).
POST_GAP_SEC = float(os.environ.get("BLOG_POST_GAP_SEC", "5"))

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
        ],
    },
]


def _key_label(api_keys: list[str], key: str) -> str:
    try:
        return f"Key#{api_keys.index(key) + 1}"
    except ValueError:
        return f"{key[:8]}…"


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
        "เคล็ดลับ": "home cleaning tips, tidy living space, realistic photo",
        "ธุรกิจ": "professional office or commercial cleaning team, B2B setting, realistic photo",
        "คู่มือ": "checklist planning cleaning service, professional tools, realistic photo",
    }
    hint = scene_hints.get(category, "professional cleaning service, realistic photo")
    return (
        f"Photorealistic cover photo for a Thai cleaning-service blog article. "
        f"Topic: {keyword}. Title context: {title}. Category: {category}. "
        f"Scene: {hint}. Natural lighting, high quality, no text, no logos, no watermarks, "
        f"no UI overlays, suitable as a website blog hero image, 16:9 composition."
    )


def _fallback_image_url() -> str:
    return f"{SITE_URL}/og-image.png"


def _save_cover(api_key: str, api_keys: list[str], slug: str, title: str, keyword: str, category: str) -> str:
    """Generate and save cover; return absolute site URL (or brand fallback)."""
    label = _key_label(api_keys, api_key)
    prompt = _image_prompt(title, keyword, category)
    raw = call_gemini_image(api_key, prompt, key_label=label)
    if not raw:
        print(f"  cover fallback → og-image.png ({slug})")
        return _fallback_image_url()

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    # Detect PNG vs JPEG from magic bytes
    ext = "png" if raw[:8].startswith(b"\x89PNG") else "jpg"
    filename = f"{slug}.{ext}"
    path = IMAGES_DIR / filename
    path.write_bytes(raw)
    url = f"{SITE_URL}/blog/images/{filename}"
    print(f"  cover saved → blog/images/{filename} ({len(raw)} bytes)")
    return url


def generate_one_post(api_keys: list[str], category: str, keyword: str, key_offset: int, existing_titles: set[str]):
    key = _pick_key(api_keys, key_offset)
    if not key:
        print("All API keys exhausted — stop generating.")
        return None, "quota"

    label = _key_label(api_keys, key)
    print(f"[{category}] {keyword} via {label}")

    result = call_gemini_json(key, _geo_prompt(keyword, category), key_label=label, timeout=90)
    if not result:
        if is_key_exhausted(key) or all(is_key_exhausted(k) for k in api_keys):
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
    # Avoid colliding filenames
    image_key = _pick_key(api_keys, key_offset) or key
    image_url = _save_cover(image_key, api_keys, slug, title, keyword, category)

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
        "geo_source": "gemini",
    }
    print(f"  OK: {title[:70]}")
    return post, "ok"


def run_daily_batch() -> int:
    api_keys = get_api_keys()
    if not api_keys:
        print("Error: GEMINI_API_KEY environment variable not found.")
        return 0

    if JSON_PATH.exists():
        with open(JSON_PATH, encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = []

    existing_titles = {p.get("title") for p in posts if p.get("title")}
    used_keywords: set[str] = set()
    added = 0
    key_offset = 0

    print(
        f"Daily GEO blogs: {POSTS_PER_CATEGORY}/category × {len(TOPICS)} categories "
        f"| keys={len(api_keys)}"
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
                api_keys, category, keyword, key_offset, existing_titles
            )
            key_offset += 1

            if status == "quota":
                print("Stopping early due to quota.")
                _write_posts(posts)
                return added
            if status != "ok" or not post:
                continue

            posts.append(post)
            existing_titles.add(post["title"])
            added += 1
            made += 1
            if POST_GAP_SEC > 0:
                time.sleep(POST_GAP_SEC)

        print(f"Category {category}: +{made}/{POSTS_PER_CATEGORY}")

    _write_posts(posts)
    print(f"Added {added} posts total.")
    return added


def _write_posts(posts: list) -> None:
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def main() -> None:
    added = run_daily_batch()
    if added <= 0:
        print("No new posts — skip rebuild.")
        return
    try:
        import build_blogs
        import update_sitemap

        build_blogs.build_blogs()
        update_sitemap.update_sitemap()
        print("Rebuild + sitemap done.")
    except Exception as exc:
        print(f"Error building static blogs or sitemap: {exc}")


if __name__ == "__main__":
    main()
