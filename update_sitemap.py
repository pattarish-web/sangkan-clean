import json
from datetime import datetime
from urllib.parse import quote

from site_config import LOCAL_AREAS, SERVICE_LANDINGS, SITE_URL


def encode_url_path(path):
    """Percent-encode path segments for valid XML sitemap URLs."""
    if not path:
        return SITE_URL + "/"
    encoded = "/".join(quote(part, safe="") for part in path.split("/"))
    return f"{SITE_URL}/{encoded}"


def url_entry(path, priority, changefreq, lastmod=None):
    lastmod = lastmod or datetime.today().strftime("%Y-%m-%d")
    loc = encode_url_path(path)
    return f"""
  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
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
    lastmod = lastmod or datetime.today().strftime("%Y-%m-%d")
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for child in child_sitemaps:
        parts.append(
            f"""
  <sitemap>
    <loc>{SITE_URL}/{child}</loc>
    <lastmod>{lastmod}</lastmod>
  </sitemap>"""
        )
    parts.append("\n</sitemapindex>\n")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("".join(parts))


def update_sitemap():
    today = datetime.today().strftime("%Y-%m-%d")

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

    page_urls = [url_entry(path, prio, freq, today) for path, prio, freq in static_pages]

    for area in LOCAL_AREAS:
        page_urls.append(url_entry(f"areas/{area['file']}.html", "0.75", "monthly", today))

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    blog_urls = []
    for post in posts:
        slug = post.get("slug")
        if not slug:
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
        # Prefer today's lastmod when the HTML file exists (reflects recent SEO/GEO edits)
        date = today
        blog_urls.append(url_entry(blog_path, "0.7", "monthly", date))

    write_urlset("sitemap-pages.xml", page_urls)
    write_urlset("sitemap-blog.xml", blog_urls)
    write_sitemap_index("sitemap.xml", ["sitemap-pages.xml", "sitemap-blog.xml"], today)

    total = len(page_urls) + len(blog_urls)
    print(
        f"Updated sitemap index: {len(page_urls)} pages + {len(blog_urls)} posts "
        f"= {total} URLs ({SITE_URL})."
    )


if __name__ == "__main__":
    update_sitemap()
