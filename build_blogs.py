import hashlib
import json
import os
import re

from build_assets import write_analytics_js
from site_config import SITE_URL, analytics_script_tag


def slugify(text):
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"[^\w\u0E00-\u0E7F\-]", "", text)
    return text.lower()


def stable_related_posts(posts, current_idx, count=3):
    current = posts[current_idx]
    category = current.get("category", "")
    pool = [p for i, p in enumerate(posts) if i != current_idx and p.get("slug")]
    same_cat = [p for p in pool if p.get("category") == category]
    others = [p for p in pool if p not in same_cat]
    ordered = same_cat + others

    seed = int(hashlib.md5(current.get("slug", "").encode()).hexdigest(), 16)
    picks = []
    for i, post in enumerate(ordered):
        if len(picks) >= count:
            break
        if (seed + i) % max(len(ordered) // count, 1) == 0 or len(picks) < count:
            if post not in picks:
                picks.append(post)
    for post in ordered:
        if len(picks) >= count:
            break
        if post not in picks:
            picks.append(post)
    return picks[:count]


def build_related_posts_html(posts, current_idx, count=3):
    picks = stable_related_posts(posts, current_idx, count)
    if not picks:
        return ""

    cards = []
    for post in picks:
        cards.append(
            f'<a href="{post["slug"]}.html" class="related-card">'
            f'<img src="{post["image"]}" alt="{post["title"]}" loading="lazy" width="120" height="80">'
            f"<div><h4>{post['title']}</h4><span>{post['date']}</span></div></a>"
        )

    return (
        '<aside class="related-posts"><h3>บทความที่เกี่ยวข้อง</h3>'
        f'<div class="related-grid">{"".join(cards)}</div></aside>'
    )


def _strip_tags(text):
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_faq_schema(content):
    """Build FAQPage schema from common GEO/Gemini/offline FAQ HTML shapes."""
    if "คำถามที่พบบ่อย" not in content and "FAQ" not in content:
        return ""

    pairs = []

    # Offline / some Gemini: <h3>Q</h3><p>A</p>
    for q, a in re.findall(
        r"<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        pairs.append((_strip_tags(q), _strip_tags(a)))

    # Gemini / offline: <p><strong>ถาม: ...</strong><br>ตอบ: ...</p>
    # Also legacy matrix: <p><strong>Q: ...</strong><br>A: ...</p>
    for block in re.findall(r"<p[^>]*>\s*<strong>(.*?)</strong>(.*?)</p>", content, flags=re.I | re.S):
        strong, rest = block
        strong_clean = _strip_tags(strong)
        answer = _strip_tags(rest)
        m = re.match(
            r"^(?:ถาม|Q)\s*[:：]\s*(.+)$",
            strong_clean,
            flags=re.IGNORECASE,
        )
        if not m:
            continue
        question = m.group(1).strip()
        answer = re.sub(r"^(?:ตอบ|A)\s*[:：]\s*", "", answer, flags=re.IGNORECASE).strip()
        if question and answer:
            pairs.append((question, answer))

    # Dedupe while preserving order
    seen = set()
    entities = []
    for q, a in pairs:
        if not q or not a or len(q) < 4 or len(a) < 4:
            continue
        key = (q.lower(), a.lower())
        if key in seen:
            continue
        seen.add(key)
        entities.append(
            {
                "@type": "Question",
                "name": q[:200],
                "acceptedAnswer": {"@type": "Answer", "text": a[:1000]},
            }
        )
        if len(entities) >= 6:
            break

    if not entities:
        return ""
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'


def prune_orphan_blogs(valid_slugs):
    if not os.path.isdir("blog"):
        return 0
    removed = 0
    for name in os.listdir("blog"):
        if not name.endswith(".html"):
            continue
        slug = name[:-5]
        if slug not in valid_slugs:
            os.remove(os.path.join("blog", name))
            removed += 1
    return removed


def render_blog_html(posts, idx, template):
    post = posts[idx]
    slug = post.get("slug") or slugify(post["title"]) or f"post-{idx}"
    post["slug"] = slug

    content = post.get("content", "")
    if not content:
        content = f"""<p>{post['description']}</p>
                   <p>บทความนี้กำลังอยู่ในระหว่างการจัดทำเนื้อหาเพิ่มเติม โปรดติดตามอัปเดตจากเราได้เร็วๆ นี้ครับ</p>
                   <p>สนใจสอบถามบริการทำความสะอาดเพิ่มเติม ติดต่อทีมงาน Sangkan Clean ได้เลยครับ</p>"""

    related = build_related_posts_html(posts, idx)
    canonical = f"{SITE_URL}/blog/{slug}.html"
    date_modified = post.get("dateModified", post.get("date", ""))
    word_count = len(re.sub(r"<[^>]+>", " ", content).split())
    faq_schema = extract_faq_schema(content)

    html = template
    replacements = {
        "{{title}}": post["title"],
        "{{description}}": post["description"],
        "{{image}}": post["image"],
        "{{category}}": post.get("category", "บทความ"),
        "{{date}}": post.get("date", ""),
        "{{date_modified}}": date_modified,
        "{{word_count}}": str(word_count),
        "{{slug}}": slug,
        "{{content}}": content,
        "{{canonical}}": canonical,
        "{{related_posts}}": related,
        "{{faq_schema}}": faq_schema,
        "{{analytics_script}}": analytics_script_tag("../"),
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    return slug, html


def build_single_blog(posts, idx):
    """Build one blog HTML file (used for per-post checkpoint saves)."""
    if not os.path.exists("blog"):
        os.makedirs("blog")
    with open("blog_template.html", "r", encoding="utf-8") as f:
        template = f.read()
    slug, html = render_blog_html(posts, idx, template)
    filepath = os.path.join("blog", f"{slug}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return slug


def build_blogs():
    if not os.path.exists("blog"):
        os.makedirs("blog")

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    with open("blog_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    updated_posts = []
    valid_slugs = set()

    for i, post in enumerate(posts):
        slug, html = render_blog_html(posts, i, template)
        valid_slugs.add(slug)

        filepath = os.path.join("blog", f"{slug}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        updated_posts.append(post)

    removed = prune_orphan_blogs(valid_slugs)

    with open("posts.json", "w", encoding="utf-8") as f:
        json.dump(updated_posts, f, ensure_ascii=False, indent=2)

    write_analytics_js()
    print(f"Generated {len(updated_posts)} static blog posts in blog/ directory.")
    if removed:
        print(f"Removed {removed} orphan blog HTML files.")


if __name__ == "__main__":
    build_blogs()
