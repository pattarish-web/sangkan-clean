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
    # Load keywords
    with open("seo/keywords.json", "r", encoding="utf-8") as f:
        keywords = json.load(f)
    posts_dir = Path("posts")
    posts_dir.mkdir(exist_ok=True)
    for entry in keywords:
        kw = entry.get("keyword")
        vol = entry.get("search_volume", 0)
        title, body = generate_post(kw, vol)
        # slugify keyword for filename
        slug = kw.replace(" ", "_").replace("/", "_")
        file_path = posts_dir / f"{slug}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{body}\n")
        print(f"Generated post: {file_path}")

if __name__ == "__main__":
    main()
