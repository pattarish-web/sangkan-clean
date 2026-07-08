import json
import os
import time

from gemini_api import call_gemini_json


def get_api_keys():
    raw_key = os.environ.get("GEMINI_API_KEY", "")
    if not raw_key:
        return []
    if "," in raw_key:
        return [k.strip() for k in raw_key.split(",") if k.strip()]
    return [raw_key.strip()]


def generate_geo_content(api_key, title, description):
    prompt = f"""
    คุณเป็นผู้เชี่ยวชาญด้านการทำความสะอาดและนักเขียนบทความ SEO/GEO (Generative Engine Optimization)
    ช่วยเขียนบทความบล็อกภาษาไทยแบบเจาะลึก
    
    ชื่อบทความ: "{title}"
    คำอธิบาย: "{description}"
    
    ข้อกำหนด (สำคัญมากสำหรับการทำ GEO เพื่อให้ AI นำไปอ้างอิง):
    เนื้อหาบทความ (content) ต้องเป็นโค้ด HTML semantic ล้วนๆ (ไม่ต้องมี <html> <body> tag)
    - <h2>สรุปประเด็นสำคัญ (Key Takeaways)</h2> ตามด้วย <ul><li> 3-4 ข้อสั้นๆ
    - <h2>เนื้อหาหลัก</h2> อธิบายเนื้อหาแบบเจาะลึก มีการใช้ <strong> เพื่อเน้นคำสำคัญ
    - <h2>ข้อมูลสถิติที่น่าสนใจ</h2> สร้างข้อมูลเชิงประมาณหรือแนวโน้มทั่วไปในอุตสาหกรรม (ไม่ใช่ตัวเลขเฉพาะบริษัท) พร้อมข้อความว่า "ข้อมูลโดยประมาณจากแนวโน้มอุตสาหกรรม"
    - <h2>คำถามที่พบบ่อย (FAQ)</h2> ถามตอบ 2-3 ข้อแบบสั้นๆ ตรงประเด็น
    
    ตอบกลับเป็น JSON format เท่านั้น:
    {{"content": "<h2>สรุปประเด็น...</h2>..."}}
    """

    parsed_result = call_gemini_json(api_key, prompt)
    if not parsed_result:
        print(f"  -> Failed to generate content for '{title}'")
        return None

    content = parsed_result.get("content", "")
    if content:
        print(f"  -> Success! Generated {len(content)} characters")
    return content or None


def upgrade_posts():
    api_keys = get_api_keys()
    if not api_keys:
        print("Error: GEMINI_API_KEY not found")
        return

    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)

    pending = [p for p in posts if "สรุปประเด็นสำคัญ" not in p.get("content", "")]
    print(f"Found {len(api_keys)} API key(s)")
    print(f"Total posts: {len(posts)}, need upgrade: {len(pending)}")

    upgraded_count = 0
    skipped_count = 0
    failed_count = 0
    key_index = 0

    for idx, post in enumerate(posts):
        content = post.get("content", "")

        if "สรุปประเด็นสำคัญ" not in content:
            print(f"\n[{idx+1}/{len(posts)}] Upgrading: {post['title'][:50]}...")

            current_key = api_keys[key_index % len(api_keys)]
            new_content = generate_geo_content(current_key, post['title'], post['description'])
            key_index += 1

            if new_content and "สรุปประเด็นสำคัญ" in new_content:
                post['content'] = new_content
                from datetime import datetime
                post['dateModified'] = datetime.today().strftime("%Y-%m-%d")
                upgraded_count += 1

                with open('posts.json', 'w', encoding='utf-8') as f:
                    json.dump(posts, f, ensure_ascii=False, indent=2)

                sleep_time = 4 if len(api_keys) > 1 else 12
                print(f"  -> Saved! Waiting {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print("  -> Failed - Skipping...")
                failed_count += 1
        else:
            skipped_count += 1

    print(f"\n{'='*60}")
    print("UPGRADE COMPLETE!")
    print(f"  Upgraded: {upgraded_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Failed: {failed_count}")
    print(f"{'='*60}\n")

    if upgraded_count > 0:
        try:
            import build_site
            build_site.build_all()
            print("HTML, local pages, and sitemap rebuilt successfully.")
        except Exception as e:
            print(f"Error rebuilding: {e}")


if __name__ == "__main__":
    upgrade_posts()
