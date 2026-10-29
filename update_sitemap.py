import json
from pathlib import Path
import re
from urllib.parse import quote

from site_config import LOCAL_AREAS, SERVICE_LANDINGS, SITE_URL


def encode_url_path(path):
    """Percent-encode path segments for valid XML sitemap URLs."""
    if not path:
        return SITE_URL + "/"
    encoded = "/".join(quote(part, safe="") for part in path.split("/"))
    return f"{SITE_URL}/{encoded}"


def content_lastmod(path, registry, published=None):
    dates = [date for date in (registry.get(path or 'index.html'), published)
             if isinstance(date, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', date)]
    return max(dates) if dates else None


def url_entry(path, priority, changefreq, lastmod=None):
    lastmod_xml = f"\n    <lastmod>{lastmod}</lastmod>" if lastmod else ""
    loc = encode_url_path(path)
    return f"""
  <url>
    <loc>{loc}</loc>{lastmod_xml}
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""


def write_urlset(filename, entries):
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(entries)
        + "\n</urlset>\n"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def write_sitemap_index(filename, child_sitemaps, lastmod=None):
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for child in child_sitemaps:
        dates = re.findall(r'<lastmod>([^<]+)</lastmod>', Path(child).read_text(encoding='utf-8'))
        child_date = max(dates) if dates else lastmod
        date_xml = f"\n    <lastmod>{child_date}</lastmod>" if child_date else ""
        parts.append(
            f"""
  <sitemap>
    <loc>{SITE_URL}/{child}</loc>{date_xml}
  </sitemap>"""
        )
    parts.append("\n</sitemapindex>\n")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("".join(parts))


def update_sitemap():
    registry_path = Path('seo/content_lastmod.json')
    registry = json.loads(registry_path.read_text(encoding='utf-8')) if registry_path.exists() else {}

    static_pages = [
        ("", "1.0", "weekly"),
        ("blog.html", "0.9", "daily"),
        ("privacy.html", "0.3", "yearly"),
        ("landing-bigcleaning.html", "0.8", "monthly"),
        ("landing-maid.html", "0.8", "monthly"),
        ("landing-sangkan-office.html", "0.8", "monthly"),
    ]

    for svc in SERVICE_LANDINGS:
        static_pages.append((f"{svc['file']}.html", "0.75", "monthly"))

    page_urls = [url_entry(path, prio, freq, content_lastmod(path, registry)) for path, prio, freq in static_pages]

    for area in LOCAL_AREAS:
        path = f"areas/{area['file']}.html"
        page_urls.append(url_entry(path, "0.75", "monthly", content_lastmod(path, registry)))

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    blog_urls = []
    from seo.redirects_util import redirect_from_slugs

    blocked = redirect_from_slugs()
    for post in posts:
        slug = post.get("slug")
        if not slug or slug in blocked:
            continue
        blog_path = f"blog/{slug}.html"
        # Skip soft-redirect stubs so sitemap only lists indexable content
        try:
            with open(blog_path, encoding="utf-8") as bf:
                head = bf.read(2500).lower()
        except OSError:
            continue
        if 'http-equiv="refresh"' in head or "location.replace" in head:
            continue
        date = content_lastmod(blog_path, registry, post.get('dateModified') or post.get('date'))
        blog_urls.append(url_entry(blog_path, "0.7", "monthly", date))

    write_urlset("sitemap-pages.xml", page_urls)
    write_urlset("sitemap-blog.xml", blog_urls)
    write_sitemap_index("sitemap.xml", ["sitemap-pages.xml", "sitemap-blog.xml"])

    total = len(page_urls) + len(blog_urls)
    print(
        f"Updated sitemap index: {len(page_urls)} pages + {len(blog_urls)} posts "
        f"= {total} URLs ({SITE_URL})."
    )


if __name__ == "__main__":
    update_sitemap()
