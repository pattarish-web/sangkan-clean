import json
import os
import random
import datetime
from pathlib import Path

# A curated list of 35 high-quality Unsplash image IDs related to cleaning, houses, offices, and buildings.
image_pool = [
    "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1563453392212-326f5e854473?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1524813686514-a57563d77965?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1497366811353-6870744d04b2?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1565538810643-b5bdb714032a?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1621905252507-b35492cc74b4?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1556910103-1c02745aae4d?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1542889601-399c4f3a8402?auto=format&fit=crop&w=600&q=80",
    "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?auto=format&fit=crop&w=600&q=80"
]

last_used_images = []

def get_unique_image():
    global last_used_images
    available = [img for img in image_pool if img not in last_used_images]
    if not available:
        available = image_pool # fallback if somehow exhausted
    
    selected = random.choice(available)
    last_used_images.append(selected)
    if len(last_used_images) > 20:
        last_used_images.pop(0)
        
    return selected

def gen_intro(kw):
    prefix = "" if kw.startswith("บริการ") else "บริการ "
    return random.choice([
        f"<p>กำลังเจอปัญหาเรื่องความสกปรกอยู่หรือเปล่า? {prefix}<strong>{kw}</strong> ของ <strong>Sangkan Clean</strong> พร้อมเป็นผู้ช่วยเบอร์หนึ่งของคุณ ด้วยทีมงานมืออาชีพที่พร้อมเข้าจัดการทุกปัญหา</p>",
        f"<p>สัมผัสประสบการณ์ความสะอาดเหนือระดับกับ <strong>{kw}</strong> จากทีมงาน <em>Sangkan Clean</em> ที่มีประสบการณ์กว่า 30 ปี เราพร้อมเปลี่ยนพื้นที่ของคุณให้กลับมาน่าอยู่และปลอดภัย</p>",
        f"<p>ถ้าคุณกำลังหาคนดูแลเรื่อง <strong>{kw}</strong> คุณมาถูกที่แล้วครับ! เราเชี่ยวชาญด้านการจัดการความสะอาดแบบครบวงจร ไม่ว่าจะเป็นคราบฝังลึกหรือฝุ่นสะสม เราจัดการได้หมด</p>",
        f"<p>ยินดีต้อนรับสู่{prefix}<strong>{kw}</strong> มาตรฐานพรีเมียมจาก <strong>Sangkan Clean</strong> ผู้นำด้านการทำความสะอาดที่ได้รับความไว้วางใจจากลูกค้ากว่า 5,000 รายทั่วประเทศ</p>"
    ])

def gen_benefits(kw):
    items = random.sample([
        "พนักงานทุกคนผ่านการอบรมอย่างเข้มงวด",
        "ใช้น้ำยาทำความสะอาดเกรดพรีเมียม ปลอดภัยไร้สารตกค้าง",
        "อุปกรณ์ทันสมัยนำเข้าจากต่างประเทศ",
        "มีประกันความเสียหายระหว่างการทำงานเต็มวงเงิน",
        "ราคาโปร่งใส คุ้มค่า ไม่มีบวกเพิ่มหน้างาน",
        "เข้างานตรงเวลา ทำงานเสร็จไว ตรวจสอบได้"
    ], 3)
    lis = "".join([f"<li style='margin-bottom: 0.5rem;'><i class='fa-solid fa-check text-success'></i> {i}</li>" for i in items])
    return f"""
    <div style="background: #f8fafc; padding: 1.5rem; border-radius: 12px; margin: 2rem 0; border-left: 4px solid #0d9488;">
        <h4 style="color: #0d9488; margin-top: 0; margin-bottom: 1rem;">ทำไมต้องเลือกเรา?</h4>
        <ul style="list-style: none; padding: 0; margin: 0;">{lis}</ul>
    </div>
    """

def gen_process(kw):
    items = random.sample([
        "ประเมินพื้นที่และวางแผนงานล่วงหน้า",
        "เตรียมอุปกรณ์และน้ำยาเฉพาะทางให้พร้อม",
        "ลงมือทำความสะอาดเชิงลึกทุกซอกมุม",
        "กำจัดเชื้อโรคและแบคทีเรียด้วยน้ำยาฆ่าเชื้อ",
        "ตรวจสอบคุณภาพ (QC) โดยหัวหน้างานก่อนส่งมอบ"
    ], 3)
    lis = "".join([f"<li style='margin-bottom: 0.8rem;'><strong>ขั้นตอน:</strong> {i}</li>" for i in items])
    return f"""
    <h3 style="color: #0f172a; margin-top: 2rem;">ขั้นตอนการทำงานของเรา</h3>
    <ol style="padding-left: 1.5rem; color: #475569;">{lis}</ol>
    """

def gen_why_important(kw):
    prefix = "" if kw.startswith("บริการ") else "บริการ "
    paras = [
        f"<p>รู้หรือไม่ว่าการละเลย <strong>{kw}</strong> อาจส่งผลเสียต่อสุขภาพของผู้อยู่อาศัยหรือพนักงานได้ ฝุ่นละอองและไรฝุ่นที่สะสมเป็นสาเหตุหลักของโรคภูมิแพ้ การให้ผู้เชี่ยวชาญเข้ามาดูแลจึงเป็นการลงทุนที่คุ้มค่าที่สุด</p>",
        f"<p>ภาพลักษณ์ที่ดีเริ่มต้นที่ความสะอาด! การใช้{prefix}<strong>{kw}</strong> อย่างสม่ำเสมอไม่เพียงแต่ช่วยยืดอายุการใช้งานของเฟอร์นิเจอร์และพื้นผิวต่างๆ แต่ยังสร้างความประทับใจแรกพบให้กับแขกหรือลูกค้าที่มาเยือนอีกด้วย</p>",
        f"<p>หลายคนมักคิดว่าการทำความสะอาดเองนั้นประหยัดกว่า แต่ในความเป็นจริงแล้ว <strong>{kw}</strong> ต้องอาศัยความชำนาญและเครื่องมือเฉพาะทาง การจ้างมืออาชีพจะช่วยประหยัดเวลาและได้ผลลัพธ์ที่สมบูรณ์แบบกว่าอย่างเห็นได้ชัด</p>"
    ]
    return random.choice(paras)

def gen_faq(kw):
    qa = [
        ("ต้องเตรียมอุปกรณ์อะไรไหม?", "ไม่ต้องเลยครับ ทีมงานของเราเตรียมอุปกรณ์และน้ำยาไปครบจบในตัว"),
        ("ใช้เวลาทำงานนานแค่ไหน?", "ขึ้นอยู่กับขนาดพื้นที่ครับ แต่เราทำงานอย่างเป็นระบบ ทำให้เสร็จรวดเร็วตามกำหนดแน่นอน"),
        ("รับประกันงานไหม?", "เรารับประกันความพึงพอใจ หากไม่เรียบร้อย เรายินดีแก้ไขให้ทันที"),
        ("น้ำยาที่ใช้ปลอดภัยไหม?", "เราเลือกใช้น้ำยาที่เป็นมิตรต่อสิ่งแวดล้อม ปลอดภัยต่อเด็กและสัตว์เลี้ยง 100%")
    ]
    selected_qa = random.sample(qa, 2)
    faqs = "".join([f"<p><strong>Q: {q}</strong><br>A: {a}</p>" for q, a in selected_qa])
    return f"<h3 style='color: #0f172a; margin-top: 2rem;'>คำถามที่พบบ่อย (FAQ)</h3>{faqs}"

def gen_outro(kw):
    return random.choice([
        f"<p style='margin-top: 2rem; padding: 1.5rem; border: 1px solid #e2e8f0; border-radius: 8px;'><strong>อย่ารอช้า!</strong> ทักหา <em>Sangkan Clean</em> วันนี้ เพื่อรับโปรโมชั่นพิเศษสำหรับ <strong>{kw}</strong> พร้อมคืนความสะอาดสดใสให้กับพื้นที่ของคุณ</p>",
        f"<p style='margin-top: 2rem; font-weight: 600; color: #0f172a;'>จบทุกปัญหาความสะอาดด้วย <strong>{kw}</strong> จาก Sangkan Clean ติดต่อประเมินราคาฟรีได้เลยครับ!</p>"
    ])

def generate_post(keyword):
    if keyword.startswith("บริการ"):
        title = f"{keyword} ระดับมืออาชีพ – Sangkan Clean"
    else:
        title = f"บริการ {keyword} ระดับมืออาชีพ – Sangkan Clean"
    
    # Randomly select a structure (mix of 3-5 modules)
    modules = [
        gen_intro(keyword),
        gen_why_important(keyword),
        gen_benefits(keyword),
        gen_process(keyword),
        gen_faq(keyword),
        gen_outro(keyword)
    ]
    
    # Shuffle modules 2,3,4 to create massive variation in structure
    middle = [modules[1], modules[2], modules[3], modules[4]]
    random.shuffle(middle)
    
    # Keep intro first, outro last, pick 2 or 3 middle sections
    num_middle = random.randint(2, 4)
    selected_middle = middle[:num_middle]
    
    final_html = modules[0] + "\n".join(selected_middle) + modules[5]
    content = f"<div style='font-size: 1.05rem; line-height: 1.8; color: #334155;'>{final_html}</div>"
    
    return title, content

def main():
    # Guard: regenerating from keywords historically wiped Gemini/offline GEO posts.
    if os.environ.get("SEO_ALLOW_OVERWRITE") != "1":
        existing_path = Path("posts.json")
        if existing_path.exists():
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            protected = sum(
                1
                for p in existing
                if p.get("geo_source") in ("gemini", "offline")
                or "สรุปประเด็นสำคัญ" in p.get("content", "")
            )
            if protected:
                raise SystemExit(
                    f"ABORT: refusing to overwrite posts.json "
                    f"({protected} GEO/protected posts). "
                    f"Set SEO_ALLOW_OVERWRITE=1 to force."
                )

    with open("seo/keywords.json", "r", encoding="utf-8") as f:
        keywords = json.load(f)
        
    posts_data = []

    posts_dir = Path("posts")
    posts_dir.mkdir(exist_ok=True)
    
    for entry in keywords:
        kw = entry.get("keyword")
        title, body = generate_post(kw)
        
        slug = kw.replace(" ", "_").replace("/", "_")
        file_path = posts_dir / f"{slug}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")
            
        img_url = get_unique_image()
        
        new_post = {
            "title": title,
            "description": f"เจาะลึกบริการ {kw} ครบวงจรด้วยทีมงานมืออาชีพ มาตรฐานระดับสากล เพื่อความสะอาดและสุขอนามัยที่ดีของคุณ",
            "category": "บริการ",
            "image": img_url,
            "date": datetime.datetime.today().strftime('%Y-%m-%d'),
            "content": body
        }
        posts_data.append(new_post)
            
    with open("posts.json", "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)
        
    print(f"Generated {len(posts_data)} completely unique posts!")

if __name__ == "__main__":
    main()
