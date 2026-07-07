import json
import os
import time
import requests

def get_api_keys():
    raw_key = os.environ.get("GEMINI_API_KEY", "")
    if not raw_key:
        return []
    if "," in raw_key:
        return [k.strip() for k in raw_key.split(",") if k.strip()]
    return [raw_key.strip()]

def generate_geo_content(api_key, title, description):
    # ← ลองใช้ gemini-pro (รุ่นเก่า แต่ใช้ได้)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    คุณเป็นผู้เชี่ยวชาญด้านการทำความสะอาดและนักเขียนบทความ SEO/GEO (Generative Engine Optimization)
    ช่วยเขียนบทความบล็อกภาษาไทยแบบเจาะลึก
    
    ชื่อบทความ: "{title}"
    คำอธิบาย: "{description}"
    
    ข้อกำหนด (สำคัญมากสำหรับการทำ GEO เพื่อให้ AI นำไปอ้างอิง):
    เนื้อหาบทความ (content) ต้องเป็นโค้ด HTML semantic ล้วนๆ (ไม่ต้องมี <html> <body> tag)
    - <h2>สรุปประเด็นสำคัญ (Key Takeaways)</h2> ตามด้วย <ul><li> 3-4 ข้อสั้นๆ
    - <h2>เนื้อหาหลัก</h2> อธิบายเนื้อหาแบบเจาะลึก มีการใช้ <strong> เพื่อเน้นคำสำคัญ
    - <h2>ข้อมูลสถิติที่น่าสนใจ</h2> บังคับให้สร้างตัวเลขสถิติหรือข้อเท็จจริง
    - <h2>คำถามที่พบบ่อย (FAQ)</h2> ถามตอบ 2-3 ข้อแบบสั้นๆ ตรงประเด็น
    
    ตอบกลับเป็น JSON format เท่านั้น:
    {{"content": "<h2>สรุปประเด็น...</h2>..."}}
    """
    
    data = {
        "contents": [{"parts":[{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }
    
    max_retries = 3
    base_delay = 15
    
    for attempt in range(max_retries):
        try:
            print(f"  -> API Call (attempt {attempt+1}/3)...")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"  -> Response Status: {response.status_code}")
            
            # ถ้าชนลิมิต หรือโควตาหมดชั่วคราว
            if response.status_code == 429 or (response.status_code == 400 and "RESOURCE_EXHAUSTED" in response.text):
                wait_time = base_delay * (1.5 ** attempt)
                print(f"  -> Rate limit hit. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                continue
            
            # 404 หรือ error อื่นๆ
            if response.status_code != 200:
                print(f"  -> API Error {response.status_code}: {response.text[:200]}")
                if response.status_code == 404:
                    print(f"  -> 404 Not Found - Model หรือ URL อาจไม่ถูกต้อง")
                response.raise_for_status()
                
            result_json = response.json()
            
            # ดึง text จากผลลัพธ์
            if 'candidates' in result_json and len(result_json['candidates']) > 0:
                text_response = result_json['candidates'][0]['content']['parts'][0]['text']
                
                # ลองแปลง JSON
                try:
                    parsed_result = json.loads(text_response)
                    content = parsed_result.get("content", "")
                    if content:
                        print(f"  -> ✅ Success! Generated {len(content)} characters")
                        return content
                except json.JSONDecodeError:
                    # ถ้า parse ไม่ได้ ลองใช้ text เลย
                    print(f"  -> JSON parse failed, using text directly")
                    return text_response
            
        except requests.exceptions.Timeout:
            print(f"  -> Request timeout")
            if attempt < max_retries - 1:
                wait_time = base_delay * (1.5 ** attempt)
                print(f"  -> Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"  -> Error: {str(e)[:100]}")
            if attempt < max_retries - 1:
                wait_time = base_delay * (1.5 ** attempt)
                print(f"  -> Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            
    print(f"  -> ❌ Failed after {max_retries} attempts")
    return None

def upgrade_posts():
    api_keys = get_api_keys()
    if not api_keys:
        print("❌ Error: GEMINI_API_KEY not found")
        return
    
    print(f"✅ Found {len(api_keys)} API key(s)")
    
    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)

    print(f"📚 Total posts: {len(posts)}")
    
    upgraded_count = 0
    skipped_count = 0
    failed_count = 0
    key_index = 0
    
    for idx, post in enumerate(posts):
        content = post.get("content", "")
        
        if "สรุปประเด็นสำคัญ" not in content:
            print(f"\n[{idx+1}/{len(posts)}] 🔄 Upgrading: {post['title'][:50]}...")
            
            current_key = api_keys[key_index % len(api_keys)]
            new_content = generate_geo_content(current_key, post['title'], post['description'])
            key_index += 1
            
            if new_content and "สรุปประเด็นสำคัญ" in new_content:
                post['content'] = new_content
                upgraded_count += 1
                
                with open('posts.json', 'w', encoding='utf-8') as f:
                    json.dump(posts, f, ensure_ascii=False, indent=2)
                
                sleep_time = 4 if len(api_keys) > 1 else 12
                print(f"  ✅ Saved! Waiting {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print(f"  ❌ Failed - Skipping...")
                failed_count += 1
        else:
            skipped_count += 1

    print(f"\n{'='*60}")
    print(f"📊 UPGRADE COMPLETE!")
    print(f"  ✅ Upgraded: {upgraded_count}")
    print(f"  ⏭️  Skipped: {skipped_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"{'='*60}\n")
    
    if upgraded_count > 0:
        try:
            import build_blogs
            build_blogs.build_blogs()
            import update_sitemap
            update_sitemap.update_sitemap()
            print("✅ HTML and Sitemap rebuilt successfully.")
        except Exception as e:
            print(f"⚠️  Error rebuilding: {e}")

if __name__ == "__main__":
    upgrade_posts()
