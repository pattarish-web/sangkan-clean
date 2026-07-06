import json
from datetime import datetime

def update_sitemap():
    base_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

  <!-- หน้าแรก -->
  <url>
    <loc>https://sangkanclean.com/</loc>
    <lastmod>2026-07-02</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>

  <!-- หน้าบทความ -->
  <url>
    <loc>https://sangkanclean.com/blog.html</loc>
    <lastmod>2026-07-02</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>

  <!-- Landing Page Big Cleaning -->
  <url>
    <loc>https://sangkanclean.com/landing-bigcleaning.html</loc>
    <lastmod>2026-07-02</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>

  <!-- Landing Page แม่บ้านประจำ -->
  <url>
    <loc>https://sangkanclean.com/landing-maid.html</loc>
    <lastmod>2026-07-02</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
"""

    with open('posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
        
    urls = []
    for post in posts:
        slug = post.get('slug')
        if not slug:
            continue
        date = post.get('date', datetime.today().strftime('%Y-%m-%d'))
        
        url_block = f"""
  <url>
    <loc>https://sangkanclean.com/blog/{slug}.html</loc>
    <lastmod>{date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>"""
        urls.append(url_block)
        
    footer = "\n</urlset>\n"
    
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(base_sitemap + "".join(urls) + footer)
        
    print(f"Updated sitemap.xml with {len(urls)} blog posts.")

if __name__ == '__main__':
    update_sitemap()
