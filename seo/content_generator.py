# seo/content_generator.py
"""
Content Generation Module
Uses OpenAI GPT‑3.5‑Turbo (free tier) to generate SEO‑optimized blog posts for each keyword.
For this demo, we simulate the AI response with placeholder text.
Generated posts are saved as Markdown files under `posts/`.
"""
import json
import os
from pathlib import Path

def generate_post(keyword, volume):
    # Simulated content – replace with actual OpenAI API call.
    title = f"{keyword.title()} – บริการทำความสะอาดจาก Sangkan Clean"
    content = f"""\
## {title}

ทำความสะอาด {keyword} เป็นหนึ่งในบริการหลักของเรา ด้วยทีมมืออาชีพและอุปกรณ์ระดับอุตสาหกรรม เรามั่นใจว่าจะส่งมอบผลลัพธ์ที่ทันสมัยและปลอดภัยสำหรับคุณ.

**การบริการที่เรามี**
- ทำความสะอาดทั่วไป
- ทำความสะอาดเชิงลึก
- บริการแม่บ้านประจำ

*ติดต่อสอบถามราคาได้ทาง Line @sangkanclean หรือโทร 02‑279‑2199*.
"""
    return title, content

def main():
    import datetime
    # Load keywords
    with open("seo/keywords.json", "r", encoding="utf-8") as f:
        keywords = json.load(f)
        
    # Load posts.json for website frontend
    posts_json_path = "posts.json"
    if os.path.exists(posts_json_path):
        with open(posts_json_path, "r", encoding="utf-8") as f:
            posts_data = json.load(f)
    else:
        posts_data = []
    
    existing_titles = [p.get("title") for p in posts_data]

    posts_dir = Path("posts")
    posts_dir.mkdir(exist_ok=True)
    
    for entry in keywords:
        kw = entry.get("keyword")
        vol = entry.get("search_volume", 0)
        title, body = generate_post(kw, vol)
        
        # Save markdown file
        slug = kw.replace(" ", "_").replace("/", "_")
        file_path = posts_dir / f"{slug}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")
            
        # Image pool (all distinct and tested)
        img_pool = [
            "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1563453392212-326f5e854473?auto=format&fit=crop&w=600&q=80",
            "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=600&q=80"
        ]
        import random

        # Add to posts.json if not exists
        if title not in existing_titles:
            new_post = {
                "title": title,
                "description": f"บริการทำความสะอาด {kw} ครบวงจรด้วยทีมงานมืออาชีพและอุปกรณ์ทันสมัย",
                "category": "บริการ",
                "image": random.choice(img_pool),
                "date": datetime.datetime.today().strftime('%Y-%m-%d')
            }
            posts_data.append(new_post)
            existing_titles.append(title)
            
    # Save updated posts.json
    with open(posts_json_path, "w", encoding="utf-8") as f:
        json.dump(posts_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
