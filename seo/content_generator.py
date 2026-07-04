import json
import os
import random
import datetime
from pathlib import Path

def generate_post(keyword, volume):
    intros = [
        f"คุณกำลังมองหาผู้เชี่ยวชาญด้าน <strong>{keyword}</strong> อยู่ใช่ไหม? ที่ <strong>Sangkan Clean</strong> เราคือผู้นำด้านบริการทำความสะอาดที่มีประสบการณ์ เราพร้อมมอบบริการที่ตอบโจทย์คุณที่สุด",
        f"ปัญหาเรื่องความสะอาดจะไม่ใช่เรื่องน่าปวดหัวอีกต่อไป! หากคุณต้องการ <strong>{keyword}</strong> ระดับมืออาชีพ <em>Sangkan Clean</em> พร้อมจัดทีมงานคุณภาพเข้าดูแลพื้นที่ของคุณในทันที",
        f"การรักษาความสะอาดคือหัวใจสำคัญของทุกสถานที่ สำหรับบริการ <strong>{keyword}</strong> เรามีทีมงานที่ผ่านการฝึกอบรมเฉพาะทาง พร้อมเครื่องมือทันสมัยที่จะช่วยเนรมิตพื้นที่ของคุณให้กลับมาเหมือนใหม่อีกครั้ง",
        f"อย่าปล่อยให้คราบสกปรกกวนใจคุณ! บริการ <strong>{keyword}</strong> จาก <strong>Sangkan Clean</strong> พร้อมตอบสนองทุกความต้องการ ไม่ว่าจะเป็นพื้นที่ขนาดเล็กหรือใหญ่ เราเอาอยู่"
    ]
    
    headers = [
        f"ทำไม {keyword} ถึงมีความสำคัญ?",
        f"เหตุผลที่คุณควรเลือกใช้บริการ {keyword} กับเรา",
        f"ความลับของ {keyword} ที่ทำให้พื้นที่ของคุณสะอาดหมดจด",
        f"ยกระดับมาตรฐานความสะอาดด้วย {keyword}"
    ]
    
    bodies = [
        f"ความสะอาดไม่เพียงแต่ส่งผลต่อภาพลักษณ์ของสถานที่ แต่ยังเกี่ยวข้องโดยตรงกับสุขภาพ บริการ <strong>{keyword}</strong> ของเราถูกออกแบบมาเพื่อกำจัดสิ่งสกปรกและเชื้อโรคที่มองไม่เห็น ด้วยมาตรฐานระดับสากล",
        f"การทำความสะอาดด้วยตัวเองอาจไม่เพียงพอและเสียเวลา บริการ <strong>{keyword}</strong> ของเราใช้เทคโนโลยีและน้ำยาเฉพาะทางที่สามารถทะลวงคราบฝังลึกได้อย่างมีประสิทธิภาพ ประหยัดเวลาและได้ผลลัพธ์ที่ดีกว่า",
        f"เราเข้าใจดีว่าแต่ละพื้นที่มีความต้องการแตกต่างกัน การทำ <strong>{keyword}</strong> ของเราจึงเริ่มต้นด้วยการประเมินหน้างานอย่างละเอียด เพื่อวางแผนการทำความสะอาดที่เหมาะสมและคุ้มค่าที่สุดสำหรับคุณ",
        f"ด้วยประสบการณ์การทำงานที่ยาวนาน บริการ <strong>{keyword}</strong> ของเราได้รับการยอมรับจากลูกค้ากว่า 5,000 องค์กรทั่วประเทศ เป็นเครื่องการันตีถึงคุณภาพและความใส่ใจในทุกตารางนิ้ว"
    ]
    
    bullets = [
        ["ทีมงานมืออาชีพที่ผ่านการฝึกอบรมมาอย่างดี", "ใช้น้ำยาทำความสะอาดที่ปลอดภัย เป็นมิตรต่อสิ่งแวดล้อม", "เครื่องมือและอุปกรณ์ที่ทันสมัย มาตรฐานโรงงาน", "รับประกันความพึงพอใจ 100%"],
        ["เข้าประเมินพื้นที่และเสนอราคาฟรี", "ไม่มีค่าใช้จ่ายแอบแฝง โปร่งใสทุกขั้นตอน", "มีประกันความเสียหายระหว่างการปฏิบัติงาน", "จัดทีมเข้าทำงานได้รวดเร็วทันใจ"],
        ["ทำความสะอาดอย่างล้ำลึกทุกซอกทุกมุม", "กำจัดเชื้อโรค แบคทีเรีย และไรฝุ่นได้ถึง 99.9%", "หัวหน้างานควบคุมคุณภาพ (QC) ทุกครั้งก่อนส่งมอบ", "บริการหลังการขายที่ใส่ใจและพร้อมดูแล"],
        ["บุคลากรไว้ใจได้ ตรวจสอบประวัติอาชญากรรมแล้วทุกคน", "ใช้น้ำยาทำความสะอาดเกรดพรีเมียม กลิ่นหอมสดชื่น", "มีความยืดหยุ่นสูง ปรับเปลี่ยนเวลาเข้างานได้ตามตกลง", "แก้ปัญหาได้ตรงจุด คราบฝังลึกแค่ไหนก็จัดการได้"]
    ]
    
    outros = [
        f"<strong>อย่าปล่อยให้ความสกปรกเป็นปัญหาของคุณอีกต่อไป!</strong> มอบความไว้วางใจให้ <em>Sangkan Clean</em> ดูแลพื้นที่ของคุณ",
        f"<strong>พร้อมหรือยังที่จะสัมผัสความสะอาดระดับพรีเมียม?</strong> ติดต่อเราวันนี้เพื่อรับคำปรึกษาและข้อเสนอพิเศษสำหรับ <em>{keyword}</em>",
        f"<strong>ความสะอาดคือจุดเริ่มต้นของสิ่งดีๆ</strong> ให้ <em>Sangkan Clean</em> เป็นผู้ดูแลพื้นที่ของคุณ เพื่อให้คุณมีเวลาไปโฟกัสกับสิ่งสำคัญ",
        f"<strong>จบทุกปัญหาความสะอาดในที่เดียว!</strong> ทักหาทีมงาน <em>Sangkan Clean</em> ตอนนี้ เราพร้อมให้บริการคุณด้วยรอยยิ้ม"
    ]

    title = f"{keyword} แบบมืออาชีพ – Sangkan Clean"
    
    intro = random.choice(intros)
    header = random.choice(headers)
    body = random.choice(bodies)
    bullet_list = random.choice(bullets)
    outro = random.choice(outros)
    
    lis = "".join([f"<li style='margin-bottom: 0.5rem;'>✅ {item}</li>" for item in bullet_list])

    content = f"""
    <div style="font-size: 1.05rem; line-height: 1.8; color: #334155;">
        <p>{intro}</p>
        
        <h3 style="color: #0f172a; margin-top: 2rem; margin-bottom: 1rem; font-weight: 700;">{header}</h3>
        <p>{body}</p>
        
        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 12px; margin: 2rem 0; border-left: 4px solid #0d9488;">
            <h4 style="color: #0d9488; margin-top: 0; margin-bottom: 1rem; font-weight: 700;">สิ่งที่คุณจะได้รับจากบริการของเรา:</h4>
            <ul style="margin-bottom: 0; padding-left: 1rem; list-style-type: none;">
                {lis}
            </ul>
        </div>
        
        <p style="margin-top: 2rem;">{outro}</p>
    </div>
    """
    return title, content

def main():
    with open("seo/keywords.json", "r", encoding="utf-8") as f:
        keywords = json.load(f)
        
    posts_data = []

    posts_dir = Path("posts")
    posts_dir.mkdir(exist_ok=True)
    
    for entry in keywords:
        kw = entry.get("keyword")
        vol = entry.get("search_volume", 0)
        title, body = generate_post(kw, vol)
        
        slug = kw.replace(" ", "_").replace("/", "_")
        file_path = posts_dir / f"{slug}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")
            
        random_id = random.randint(1, 1000)
        img_url = f"https://loremflickr.com/600/400/cleaning,maid,house,office?lock={random_id}"
        
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

if __name__ == "__main__":
    main()
