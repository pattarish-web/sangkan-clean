"""Validate crawl-critical SEO signals without modifying site content."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", *sorted(ROOT.glob("landing-*.html"))]


def required(pattern: str, html: str, path: Path, label: str) -> None:
    if not re.search(pattern, html, re.IGNORECASE | re.DOTALL):
        raise AssertionError(f"{path.relative_to(ROOT)}: missing {label}")


def check_page(path: Path) -> None:
    html = path.read_text(encoding="utf-8")
    required(r"<title\b[^>]*>[^<]+\S[^<]*</title>", html, path, "title")
    required(
        r'<meta\s+name=["\']description["\'][^>]+content=["\'][^"\']{80,}["\']',
        html,
        path,
        "description",
    )
    required(r'<meta\s+name=["\']robots["\'][^>]*>', html, path, "robots")
    required(
        r'<link\s+rel=["\']canonical["\'][^>]+href=["\']https://www\.sangkanclean\.com/',
        html,
        path,
        "canonical",
    )
    required(r"application/ld\+json", html, path, "JSON-LD")
    images = re.findall(r"<img\b[^>]+src=[\"']([^\"']+)", html, re.IGNORECASE)
    alt_count = len(re.findall(r"<img\b[^>]+\balt=[\"'][^\"']*[\"']", html, re.IGNORECASE))
    if len(images) != alt_count:
        raise AssertionError(f"{path.relative_to(ROOT)}: image missing alt text")


def page_meta(path: Path) -> tuple[str, str]:
    html = path.read_text(encoding="utf-8")
    title = re.search(r"<title\b[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    description = re.search(
        r'<meta\s+name=["\']description["\'][^>]+content=["\']([^"\']+)',
        html,
        re.IGNORECASE,
    )
    if not title or not description:
        raise AssertionError(f"{path.relative_to(ROOT)}: metadata extraction failed")
    return title.group(1).strip(), description.group(1).strip()


def check_unique_metadata() -> None:
    metadata = [page_meta(page) for page in HTML_FILES]
    for index, field in enumerate(("title", "description")):
        values = [pair[index] for pair in metadata]
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            raise AssertionError(f"duplicate {field}: {duplicates[0]}")


def check_sitemap() -> None:
    sitemap = (ROOT / "sitemap-pages.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    if len(urls) != len(set(urls)):
        raise AssertionError("sitemap-pages.xml contains duplicate URLs")
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "www.sangkanclean.com":
            raise AssertionError(f"sitemap URL is not canonical: {url}")


def main() -> int:
    try:
        for page in HTML_FILES:
            check_page(page)
        check_unique_metadata()
        check_sitemap()
    except (AssertionError, FileNotFoundError) as exc:
        print(f"SEO validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"SEO validation passed for {len(HTML_FILES)} key HTML pages and sitemap-pages.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
