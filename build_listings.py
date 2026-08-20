"""Build lightweight post index + static HTML for blog/homepage (SEO + fast load)."""

import html
import json
import re

INDEX_FIELDS = ("title", "description", "category", "image", "date", "dateModified", "slug")
PER_PAGE = 12
HOME_ARTICLES = 3


def load_posts():
    from seo.redirects_util import filter_indexable_posts

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)
    return filter_indexable_posts(posts)


def write_posts_index(posts):
    index = [{k: p.get(k) for k in INDEX_FIELDS if p.get(k) is not None} for p in posts if p.get("slug")]
    with open("posts-index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote posts-index.json ({len(index)} posts, {len(json.dumps(index, ensure_ascii=False)) // 1024} KB).")


def _card_html(post):
    slug = html.escape(post.get("slug") or "post")
    title = html.escape(post.get("title") or "")
    desc = html.escape(post.get("description") or "")
    category = html.escape(post.get("category") or "บทความ")
    date = html.escape(post.get("date") or "")
    image = html.escape(post.get("image") or "")
    return f"""<a href="blog/{slug}.html" class="blog-card">
                    <img src="{image}" alt="{title}" class="blog-card-img" loading="lazy" width="400" height="180">
                    <div class="blog-card-body">
                        <span class="blog-card-tag">{category}</span>
                        <h2 class="blog-card-title">{title}</h2>
                        <p class="blog-card-desc">{desc}</p>
                        <span style="font-size:0.78rem;color:#94a3b8;"><i class="fa-regular fa-calendar"></i> {date}</span>
                    </div>
                </a>"""


def _article_html(post):
    slug = html.escape(post.get("slug") or "post")
    title = html.escape(post.get("title") or "")
    desc = html.escape(post.get("description") or "")
    category = html.escape(post.get("category") or "บทความ")
    image = html.escape(post.get("image") or "")
    return f"""<article class="article-card">
                        <div class="article-img">
                            <img src="{image}" alt="{title}" loading="lazy" width="400" height="240">
                            <span class="article-tag">{category}</span>
                        </div>
                        <div class="article-body">
                            <h3>{title}</h3>
                            <p>{desc}</p>
                            <a href="blog/{slug}.html" class="read-more">อ่านต่อ <i class="fa-solid fa-arrow-right"></i></a>
                        </div>
                    </article>"""


def _patch_block(text, start_marker, end_marker, inner):
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    replacement = start_marker + inner + end_marker
    if not pattern.search(text):
        raise ValueError(f"Markers not found: {start_marker}")
    return pattern.sub(replacement, text, count=1)


def patch_blog_html(posts):
    ordered = list(reversed(posts))
    first_page = ordered[:PER_PAGE]
    grid_html = "".join(_card_html(p) for p in first_page)
    crawl_html = "".join(
        f'<a href="blog/{html.escape(p.get("slug") or "post")}.html">{html.escape(p.get("title") or "")}</a>'
        for p in ordered
        if p.get("slug")
    )

    with open("blog.html", "r", encoding="utf-8") as f:
        content = f.read()

    content = _patch_block(content, "<!-- STATIC_BLOG_GRID_START -->", "<!-- STATIC_BLOG_GRID_END -->", grid_html)
    content = _patch_block(content, "<!-- STATIC_CRAWL_LINKS_START -->", "<!-- STATIC_CRAWL_LINKS_END -->", crawl_html)

    with open("blog.html", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Patched blog.html with {len(first_page)} static cards + {len(ordered)} crawl links.")


def patch_index_html(posts):
    latest = list(reversed(posts))[:HOME_ARTICLES]
    articles_html = "".join(_article_html(p) for p in latest)

    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()

    content = _patch_block(content, "<!-- STATIC_ARTICLES_START -->", "<!-- STATIC_ARTICLES_END -->", articles_html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Patched index.html with {len(latest)} static articles.")


def build_listings():
    posts = load_posts()
    write_posts_index(posts)
    patch_blog_html(posts)
    patch_index_html(posts)


if __name__ == "__main__":
    build_listings()
