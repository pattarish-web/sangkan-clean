"""Add FAQ section to posts missing FAQPage schema, then rebuild blogs."""

import json
import random
import re
from datetime import datetime

from build_blogs import extract_faq_schema, slugify
from offline_geo_upgrade import FAQ_BANK

FAQ_BLOCK = """
  <h2>คำถามที่พบบ่อย (FAQ)</h2>
{items}
"""


def _faq_items_html(rng: random.Random) -> str:
  picks = rng.sample(FAQ_BANK, 3)
  lines = []
  for q, a in picks:
    lines.append(
      f'  <p><strong>ถาม: {q}</strong><br>ตอบ: {a}</p>'
    )
  return "\n".join(lines)


def ensure_faq_in_content(content: str, slug: str) -> str:
  if extract_faq_schema(content):
    return content
  if "คำถามที่พบบ่อย" in content or "FAQ" in content:
    return content

  rng = random.Random(slug)
  block = FAQ_BLOCK.format(items=_faq_items_html(rng))

  if "</article>" in content:
    return content.replace("</article>", block + "\n</article>", 1)

  return content.rstrip() + "\n" + block


def main():
  with open("posts.json", encoding="utf-8") as f:
    posts = json.load(f)

  fixed = 0
  today = datetime.now().strftime("%Y-%m-%d")
  for post in posts:
    before = post.get("content", "")
    if extract_faq_schema(before):
      continue
    slug = post.get("slug") or slugify(post.get("title", ""))
    post["content"] = ensure_faq_in_content(before, slug)
    post["dateModified"] = today
    fixed += 1

  if not fixed:
    print("No FAQ gaps to fix.")
    return

  with open("posts.json", "w", encoding="utf-8") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)

  import build_site

  build_site.rebuild_blog_surface()
  after = sum(1 for p in posts if extract_faq_schema(p.get("content", "")))
  print(f"Fixed {fixed} posts. FAQ schema coverage: {after}/{len(posts)}")


if __name__ == "__main__":
  main()
