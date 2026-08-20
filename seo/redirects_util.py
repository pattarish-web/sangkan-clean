"""Shared helpers for SEO cannibalization redirect slugs."""

from __future__ import annotations

import json
import os
from pathlib import Path

REDIRECTS_PATH = Path("seo") / "redirects.json"


def redirect_from_slugs(path: str | Path | None = None) -> set[str]:
    """Slugs that are soft-redirect sources (must not be rendered as full posts)."""
    redirects_path = Path(path) if path else REDIRECTS_PATH
    if not redirects_path.is_file():
        return set()
    try:
        rules = json.loads(redirects_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    slugs: set[str] = set()
    for rule in rules:
        from_path = rule.get("from") or ""
        if from_path.endswith(".html"):
            slugs.add(os.path.splitext(os.path.basename(from_path))[0])
    return slugs


def filter_indexable_posts(posts: list) -> list:
    """Drop posts whose slug is a redirect source."""
    blocked = redirect_from_slugs()
    if not blocked:
        return list(posts)
    out = []
    for post in posts:
        slug = post.get("slug") or ""
        if slug and slug in blocked:
            continue
        out.append(post)
    return out
