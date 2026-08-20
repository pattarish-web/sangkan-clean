"""Assert redirect stubs stay out of indexable surfaces.

Run: python seo/check_redirect_consistency.py
Exit 0 = OK, 1 = failures.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from seo.redirects_util import redirect_from_slugs  # noqa: E402


def _slugs_from_posts_json() -> list[str]:
    text = (ROOT / "posts.json").read_text(encoding="utf-8")
    return re.findall(r'"slug"\s*:\s*"((?:[^"\\]|\\.)*)"', text)


def _crawl_hrefs() -> list[str]:
    blog = (ROOT / "blog.html").read_text(encoding="utf-8")
    m = re.search(
        r"<!-- STATIC_CRAWL_LINKS_START -->(.*?)<!-- STATIC_CRAWL_LINKS_END -->",
        blog,
        flags=re.S,
    )
    if not m:
        return []
    return re.findall(r'href="blog/([^"]+)\.html"', m.group(1))


def main() -> int:
    blocked = redirect_from_slugs(ROOT / "seo" / "redirects.json")
    errors: list[str] = []

    for slug in _slugs_from_posts_json():
        if slug in blocked:
            errors.append(f"posts.json still has redirect slug: {slug}")

    for slug in _crawl_hrefs():
        if slug in blocked:
            errors.append(f"blog.html crawl link to stub: {slug}")

    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for slug in blocked:
        if f"/blog/{slug}.html" in sm:
            errors.append(f"sitemap lists stub: {slug}")

    site = "https://www.sangkanclean.com"
    for path in (ROOT / "blog").glob("*.html"):
        slug = path.stem
        if slug in blocked or slug == "index":
            continue
        text = path.read_text(encoding="utf-8")
        cm = re.search(r'rel="canonical"\s+href="([^"]+)"', text)
        if not cm:
            errors.append(f"missing canonical: {path.name}")
            continue
        canon = cm.group(1)
        expect = f"{site}/blog/{slug}.html"
        if canon != expect:
            errors.append(f"canonical mismatch {path.name}: {canon}")
        if any(f"/blog/{b}.html" == canon for b in blocked):
            errors.append(f"canonical points at stub: {path.name}")

        aside = re.search(r'<aside class="related-posts">[\s\S]*?</aside>', text)
        if aside:
            for b in blocked:
                if f'href="{b}.html"' in aside.group(0):
                    errors.append(f"related-card -> stub in {path.name}: {b}")
                    break

    # stubs exist and look like redirects
    missing_stub = 0
    for slug in blocked:
        stub = ROOT / "blog" / f"{slug}.html"
        if not stub.is_file():
            missing_stub += 1
            errors.append(f"missing stub file: {slug}")
            continue
        head = stub.read_text(encoding="utf-8")[:2500].lower()
        if 'http-equiv="refresh"' not in head and "location.replace" not in head:
            errors.append(f"stub is not a redirect: {slug}")

    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for e in errors[:50]:
            print(f"  - {e}")
        if len(errors) > 50:
            print(f"  … {len(errors) - 50} more")
        return 1

    print(
        f"OK: {len(blocked)} stubs, "
        f"{len(_slugs_from_posts_json())} posts, "
        f"no stub leaks in posts/crawl/sitemap/canonical/related"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
