"""Merge our daily blog posts.json onto origin/main after a rebase conflict."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    ours_path = Path("/tmp/ours_posts.json")
    our_commit = Path("/tmp/our_commit").read_text(encoding="utf-8").strip()
    ours = json.loads(ours_path.read_text(encoding="utf-8"))
    theirs = json.loads((ROOT / "posts.json").read_text(encoding="utf-8"))
    have = {p.get("slug") for p in theirs}
    added = [p for p in ours if p.get("slug") not in have]
    merged = theirs + added
    (ROOT / "posts.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"kept_remote={len(theirs)} added_new={len(added)} total={len(merged)}")

    for p in added:
        slug = p.get("slug") or ""
        if not slug:
            continue
        print("restore", slug)
        subprocess.run(
            ["git", "checkout", our_commit, "--", f"blog/{slug}.html"],
            check=False,
        )
        for ext in ("png", "jpg", "jpeg", "webp"):
            subprocess.run(
                ["git", "checkout", our_commit, "--", f"blog/images/{slug}.{ext}"],
                check=False,
            )

    import compose_blog_covers
    compose_blog_covers.main()

    import build_blogs
    import build_listings
    import update_sitemap

    build_blogs.build_blogs()
    build_listings.build_listings()
    update_sitemap.update_sitemap()
    print("rebuild done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
