import json
import os
from datetime import datetime

from site_config import LOCAL_AREAS, SERVICE_LANDINGS, SITE_URL


def url_entry(path, priority, changefreq, lastmod=None):
    lastmod = lastmod or datetime.today().strftime("%Y-%m-%d")
    return f"""
  <url>
    <loc>{SITE_URL}/{path}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""


def update_sitemap():
    static_pages = [
        ("", "1.0", "weekly"),
        ("blog.html", "0.9", "daily"),
        ("privacy.html", "0.3", "yearly"),
        ("landing-bigcleaning.html", "0.8", "monthly"),
        ("landing-maid.html", "0.8", "monthly"),
    ]

    for svc in SERVICE_LANDINGS:
        static_pages.append((f"{svc['file']}.html", "0.75", "monthly"))

    urls = [url_entry(path, prio, freq) for path, prio, freq in static_pages]

    for area in LOCAL_AREAS:
        urls.append(url_entry(f"areas/{area['file']}.html", "0.75", "monthly"))

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    for post in posts:
        slug = post.get("slug")
        if not slug:
            continue
        date = post.get("dateModified", post.get("date", datetime.today().strftime("%Y-%m-%d")))
        urls.append(url_entry(f"blog/{slug}.html", "0.7", "monthly", date))

    content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    content += "".join(urls)
    content += "\n</urlset>\n"

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated sitemap.xml with {len(urls)} URLs (www.sangkanclean.com).")


if __name__ == "__main__":
    update_sitemap()
