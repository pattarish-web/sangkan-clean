"""Upgrade content quality signals for SEO/GEO/AIO scoring."""

import json
import re
from datetime import date

from site_config import SITE_URL

BRAND_IMAGE = f"{SITE_URL}/og-image.jpg?v=20260824"
CTA_MARKER = "<!-- SANGKAN_CTA -->"
CTA_HTML = (
    f'{CTA_MARKER}<section class="inline-cta">'
    f"<h3>สนใจบริการทำความสะอาดครบวงจร?</h3>"
    f"<p>ทีมงาน Sangkan Clean พร้อมประเมินราคาฟรี "
    f'โทร <a href="tel:0636865134">063-686-5134</a> '
    f'หรือ LINE <a href="https://line.me/ti/p/@sangkanclean">@sangkanclean</a> '
    f"หรือขอใบเสนอราคาได้ทันที</p></section>"
)

TITLE_BRAND_SUFFIX = re.compile(
    r"\s*[–—\-]\s*Sangkan Clean\s*$",
    re.IGNORECASE,
)


def ensure_cta(content: str) -> str:
    if not content:
        content = ""
    if CTA_MARKER in content or "063-686-5134" in content or "ใบเสนอราคา" in content:
        if "063-686" not in content and "ใบเสนอราคา" not in content:
            return content.rstrip() + CTA_HTML
        return content
    return content.rstrip() + CTA_HTML


def clean_title(title: str) -> str:
    title = (title or "").strip()
    title = TITLE_BRAND_SUFFIX.sub("", title).strip()
    return title


def upgrade_posts():
    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    today = date.today().isoformat()
    changed = 0
    for post in posts:
        before = (post.get("title"), post.get("image"), post.get("content"))
        post["title"] = clean_title(post.get("title", ""))
        if "unsplash.com" in (post.get("image") or ""):
            post["image"] = BRAND_IMAGE
        post["content"] = ensure_cta(post.get("content") or "")
        post["dateModified"] = today
        after = (post.get("title"), post.get("image"), post.get("content"))
        if before != after:
            changed += 1

    with open("posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"Upgraded {changed}/{len(posts)} posts (CTA, brand images, clean titles).")


if __name__ == "__main__":
    upgrade_posts()
