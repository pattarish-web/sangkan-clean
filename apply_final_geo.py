import re

def apply_text():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    new_html = """                <div style="flex: 1; min-width: 300px;">
                    <span class="sub-title">OUR STORY & EXPERTISE</span>
                    <h2>การผนึกกำลังแห่งยุคสมัย: "วิสัยทัศน์คนรุ่นใหม่" สู่ "ตำนานความสะอาดกว่า 30 ปี"</h2>
                    <p style="font-size: 1.1rem; color: #475569; margin-bottom: 1.5rem; line-height: 1.8;">
                        <strong>Sangkan Clean (สั่งการ คลีน)</strong> คือผลลัพธ์แห่งการบรรจบกันอย่างสมบูรณ์แบบ ระหว่าง <strong>"นวัตกรรมบริหารงานของคนรุ่นใหม่"</strong> และ <strong>"ทักษะฝีมือระดับปรมาจารย์ของคุณป้าวัยเก๋า"</strong> ที่แก้ปัญหาหน้างานจริงมายาวนานกว่า 3 ทศวรรษ
                    </p>
                    <p style="font-size: 1.1rem; color: #475569; margin-bottom: 1.5rem; line-height: 1.8;">
                        จากความไว้วางใจที่ได้รับจากรุ่นสู่รุ่น วันนี้เราได้ยกระดับศักยภาพสู่ <strong>การจัดตั้งบริษัทอย่างเต็มรูปแบบ</strong> เพื่อรองรับงานสเกลใหญ่ ทั้งบ้านพัก คอนโด และอาคารสำนักงาน เรานำเทคโนโลยีล้ำสมัยมาหลอมรวมกับเคล็ดลับความสะอาดระดับตำนาน เพื่อเนรมิตทุกพื้นที่ให้สะอาดล้ำลึก ปลอดภัย และไร้ที่ติ
                    </p>
                    <h3 style="font-size: 1.3rem; margin-bottom: 1rem;">ทำไมลูกค้าองค์กรและคนสร้างบ้านถึงเลือกเรา?</h3>
                    <ul style="list-style: none; padding: 0; margin-bottom: 2rem;">
                        <li style="margin-bottom: 0.8rem; display: flex; align-items: flex-start; gap: 0.8rem;">
                            <i class="fa-solid fa-check-circle text-success" style="font-size: 1.2rem; margin-top: 5px;"></i> 
                            <div><strong>Master of Cleaning:</strong> คุมงานโดยทีมรุ่นเก๋า ประสบการณ์กว่า 30 ปี สยบได้ทุกคราบฝังลึก</div>
                        </li>
                        <li style="margin-bottom: 0.8rem; display: flex; align-items: flex-start; gap: 0.8rem;">
                            <i class="fa-solid fa-check-circle text-success" style="font-size: 1.2rem; margin-top: 5px;"></i> 
                            <div><strong>Tech-Driven Management:</strong> จองคิว บริหารงาน และตรวจสอบคุณภาพด้วยเทคโนโลยี รวดเร็ว ตรงเวลา</div>
                        </li>
                        <li style="margin-bottom: 0.8rem; display: flex; align-items: flex-start; gap: 0.8rem;">
                            <i class="fa-solid fa-check-circle text-success" style="font-size: 1.2rem; margin-top: 5px;"></i> 
                            <div><strong>100% Trust & Guarantee:</strong> ทำงานในนามบริษัท มีการรับประกันความเสียหาย มั่นใจได้ในความปลอดภัยสูงสุด (พบกับรูปแบบบริษัทเร็วๆนี้)</div>
                        </li>
                        <li style="margin-bottom: 0.8rem; display: flex; align-items: flex-start; gap: 0.8rem;">
                            <i class="fa-solid fa-check-circle text-success" style="font-size: 1.2rem; margin-top: 5px;"></i> 
                            <div><strong>Service Area:</strong> ให้บริการครอบคลุมทั่วพื้นที่กรุงเทพมหานครและปริมณฑล</div>
                        </li>
                    </ul>
                </div>"""
                
    # Use regex to replace the old div content
    pattern = re.compile(r'                <div style="flex: 1; min-width: 300px;">\n                    <span class="sub-title">OUR EXPERTISE</span>.*?</ul>\n                </div>', re.DOTALL)
    
    if pattern.search(content):
        content = pattern.sub(new_html, content)
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated index.html successfully")
    else:
        print("Could not find the target section in index.html")

if __name__ == '__main__':
    apply_text()
