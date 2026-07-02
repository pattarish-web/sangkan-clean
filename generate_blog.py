import os
import json
import random
import requests
from datetime import datetime

# CONFIGURATION
# ใน GitHub Actions เราจะใส่ GEMINI_API_KEY ไว้ใน Repository Secrets
API_KEY = os.environ.get("GEMINI_API_KEY")
JSON_PATH = os.path.join(os.path.dirname(__file__), "posts.json")

# หมวดหมู่และคำค้นหาสำหรับหัวข้อบทความทำความสะอาด (SEO keywords)
TOPICS = [
    {"category": "เคล็ดลับ", "keywords": ["ทำความสะอาดบ้าน", "ขจัดคราบห้องน้ำ", "วิธีกำจัดไรฝุ่น", "ขจัดคราบฝังลึก", "ล้างกระจกให้ใส"]},
    {"category": "ธุรกิจ", "keywords": ["จัดหาแม่บ้านประจำ", "บริษัททำความสะอาด ออฟฟิศ", "แม่บ้านสำนักงาน ดีอย่างไร", "Big Cleaning โรงงาน", "แม่บ้านคอนโด"]},
    {"category": "คู่มือ", "keywords": ["เช็คลิสต์ก่อนเลือกแม่บ้าน", "มาตรฐานบริการทำความสะอาด", "น้ำยาทำความสะอาดที่ปลอดภัย", "ทำความสะอาดหลังก่อสร้าง"]}
]

# คลังภาพ Unsplash สำหรับประกอบบทความทำความสะอาด (30+ รูป ไม่ซ้ำ)
CLEANING_IMAGES = [
    # ทีมทำความสะอาด
    "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1628177142898-93e36e4e3a50?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1563453392212-326f5e854473?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?auto=format&fit=crop&w=600&q=80",
    # ทำความสะอาดพื้น
    "https://images.unsplash.com/photo-1603712726208-49179d5b1b1a?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1581578949510-fa7315c4c350?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1501769214405-5e51ca70a9f6?auto=format&fit=crop&w=600&q=80",
    # น้ำยาและอุปกรณ์
    "https://images.unsplash.com/photo-1563453392212-326f5e854473?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1552010099-5dc86fcfaa38?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1583947215259-38e31be8751f?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?auto=format&fit=crop&w=600&q=80",
    # ห้องน้ำ / ครัว
    "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1556909172-54557c7e4fb7?auto=format&fit=crop&w=600&q=80",
    # ออฟฟิศ / อาคาร
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1486325212027-8081e485255e?auto=format&fit=crop&w=600&q=80",
    # โรงแรม / คอนโด
    "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1631049552057-403cdb8f0658?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=600&q=80",
    # สุขภาพ / ความสะอาด
    "https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1609220136736-443140cfeaa8?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?auto=format&fit=crop&w=600&q=80",
    # แม่บ้าน
    "https://images.unsplash.com/photo-1600880292089-90a7e086ee0c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1596178065887-1198b6148b2b?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1545173168-9f1947eebb7f?auto=format&fit=crop&w=600&q=80",
]

def generate_blog_post():
    if not API_KEY:
        print("Error: GEMINI_API_KEY environment variable not found.")
        return None

    # สุ่มเลือกหัวข้อ
    topic_info = random.choice(TOPICS)
    keyword = random.choice(topic_info["keywords"])
    category = topic_info["category"]

    print(f"Generating post for keyword: {keyword} in category: {category}")

    # เรียกใช้ Gemini API (Gemini 1.5 Flash เพื่อการเจนข้อความภาษาไทยที่ดีและประหยัด)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    prompt = f"""
    คุณเป็นนักเขียนบทความและผู้เชี่ยวชาญด้านการทำความสะอาดและบริการจัดหาแม่บ้าน (SEO Content Creator)
    ช่วยเขียนบทความบล็อกสั้นภาษาไทยเกี่ยวกับหัวข้อ: "{keyword}"
    
    ข้อกำหนด:
    1. ชื่อบทความ (Title): น่าสนใจ ดึงดูดคลิก และมีคำค้นหาหลัก (SEO friendly) มีความยาวไม่เกิน 100 ตัวอักษร
    2. ย่อหน้าสรุป (Description): เป็นคำอธิบายสั้นๆ ดึงดูดความสนใจผู้อ่านเพื่อเป็นข้อความพรีวิวของบทความ ความยาวประมาณ 100-150 ตัวอักษร
    
    ส่งกลับมาในรูปแบบ JSON เท่านั้น ห้ามเขียนคำอธิบายอื่นนอกเหนือจาก JSON โครงสร้างดังนี้:
    {{
      "title": "ชื่อบทความภาษาไทยที่น่าสนใจ",
      "description": "คำสรุปย่อหน้าพรีวิวภาษาไทย..."
    }}
    """

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response_json = response.json()
        
        # แกะข้อความ JSON ออกมา
        text_content = response_json["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text_content)
        
        # นำมาประกอบเป็นข้อมูลบทความสมบูรณ์
        new_post = {
            "title": result["title"],
            "description": result["description"],
            "category": category,
            "image": random.choice(CLEANING_IMAGES),
            "date": datetime.today().strftime('%Y-%m-%d')
        }
        return new_post
    except Exception as e:
        print(f"API call failed: {e}")
        return None

def update_posts_json():
    # ดึงบทความจาก AI
    new_post = generate_blog_post()
    if not new_post:
        print("Failed to generate new post.")
        return

    # อ่านไฟล์ JSON เดิม
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                posts = json.load(f)
        except Exception:
            posts = []
    else:
        posts = []

    # ป้องกันการบันทึกบทความซ้ำซ้อน
    # ตรวจสอบชื่อบทความเดิม
    existing_titles = [p.get("title") for p in posts]
    if new_post["title"] in existing_titles:
        print("Title already exists. Skipping.")
        return

    # เพิ่มบทความใหม่ลงไป
    posts.append(new_post)
    print(f"Added new post: {new_post['title']}")

    # เขียนข้อมูลทับกลับลงไป
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    update_posts_json()
