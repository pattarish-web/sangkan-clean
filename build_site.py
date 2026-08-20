"""Run all site build steps."""

import json
from pathlib import Path

import build_blogs
import build_listings
import build_local_pages
import build_service_landings
import update_sitemap
from build_assets import patch_root_html_files, write_analytics_js
from seo.cannibalization import write_redirect_files


def apply_redirect_stubs() -> int:
    """Rewrite soft-redirect HTML stubs from seo/redirects.json. Returns count written."""
    redirects_path = Path("seo/redirects.json")
    if not redirects_path.exists():
        return 0
    written = write_redirect_files(json.loads(redirects_path.read_text(encoding="utf-8")))
    # Keep Cloudflare Worker map in sync (deploy is still manual — see docs/CLOUDFLARE_REDIRECTS.md)
    try:
        from seo.generate_cloudflare_redirects import main as gen_cf

        gen_cf()
    except Exception as exc:
        print(f"Cloudflare redirect map refresh skipped: {exc}")
    return written


def rebuild_blog_surface() -> None:
    """Blogs + redirect stubs + listings + sitemap (safe for blog-bot / merge paths)."""
    build_blogs.build_blogs()
    apply_redirect_stubs()
    build_listings.build_listings()
    update_sitemap.update_sitemap()
    print("Blog surface rebuild complete.")


def build_all():
    write_analytics_js()
    patch_root_html_files()
    build_blogs.build_blogs()
    apply_redirect_stubs()
    build_listings.build_listings()
    build_local_pages.build_local_pages()
    build_service_landings.build_service_landings()
    update_sitemap.update_sitemap()
    print("Site build complete.")


if __name__ == "__main__":
    build_all()
