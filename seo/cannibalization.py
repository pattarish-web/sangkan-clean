"""Normalize matrix-blog intents and build redirect maps for SEO cannibalization."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://www.sangkanclean.com"

MATRIX_SUFFIX = "-ระดับมืออาชีพ--sangkan-clean"

# Hire-synonym prefixes → base cleaning service
HIRE_PREFIXES = (
    "จ้างทำความสะอาด",
    "รับเหมาทำความสะอาด",
    "รับทำความสะอาด",
    "หาคนทำความสะอาด",
)

# Distinct intents that must NOT collapse into general cleaning
PROTECTED_PREFIXES = (
    "ทำความสะอาดหลังก่อสร้าง",
)

LANDING_RULES = (
    # Office maid money cluster → office landing
    (re.compile(r"^แม่บ้าน(ออฟฟิศ|สำนักงาน)$"), "/landing-sangkan-office.html"),
    (re.compile(r"^หาแม่บ้าน(ออฟฟิศ|สำนักงาน)$"), "/landing-sangkan-office.html"),
    # Home maid → maid landing
    (re.compile(r"^แม่บ้านบ้าน$"), "/landing-maid.html"),
    # Generic / head Big Cleaning without needing venue blog competition with money page
    # Venue-specific บิ๊กคลีนนิ่ง{venue} stays as blog; only exact head terms if any
)


def slugify(text: str) -> str:
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"[^\w\u0E00-\u0E7F\-]", "", text)
    return text.lower()


def matrix_slug_for_keyword(keyword: str) -> str:
    """Canonical matrix slug: always 'บริการ {kw} …' so hyphens are consistent."""
    kw = keyword.strip()
    if kw.startswith("บริการ"):
        title = f"{kw} ระดับมืออาชีพ – Sangkan Clean"
    else:
        title = f"บริการ {kw} ระดับมืออาชีพ – Sangkan Clean"
    return slugify(title)


def keyword_from_matrix_slug(slug: str) -> str | None:
    if not slug.endswith(MATRIX_SUFFIX):
        return None
    core = slug[: -len(MATRIX_SUFFIX)]
    if core.startswith("บริการ-"):
        return core[len("บริการ-") :]
    if core.startswith("บริการ"):
        return core[len("บริการ") :].lstrip("-")
    return None


def keyword_from_title(title: str) -> str:
    t = re.sub(r"\s*[–—\-]\s*Sangkan Clean\s*$", "", title, flags=re.I).strip()
    t = re.sub(r"\s*ระดับมืออาชีพ\s*$", "", t).strip()
    t = re.sub(r"^บริการ\s*", "", t).strip()
    return t


def normalize_intent(keyword: str) -> str:
    """Collapse synonym/hyphen/EN-TH variants into one intent key."""
    k = keyword.strip()
    k = re.sub(r"^บริการ\s*", "", k)
    k = re.sub(r"\s+", "", k)  # Thai keywords rarely need spaces between words

    # EN Big Cleaning → Thai (space, hyphen, or glued)
    k = re.sub(r"(?i)big[\s\-]*cleaning", "บิ๊กคลีนนิ่ง", k)
    k = re.sub(r"(?i)bigcleaning", "บิ๊กคลีนนิ่ง", k)

    # Deep-clean synonym
    if k.startswith("เคลียร์พื้นที่"):
        k = "บิ๊กคลีนนิ่ง" + k[len("เคลียร์พื้นที่") :]

    # Keep post-construction distinct
    for protected in PROTECTED_PREFIXES:
        if k.startswith(protected):
            return k

    for prefix in HIRE_PREFIXES:
        if k.startswith(prefix):
            venue = k[len(prefix) :]
            return "ทำความสะอาด" + venue

    if k.startswith("หาแม่บ้าน"):
        return "แม่บ้าน" + k[len("หาแม่บ้าน") :]

    return k


def preferred_keyword(intent: str) -> str:
    """Human-facing keyword for the canonical page (no leading บริการ)."""
    return intent


def landing_target(intent: str) -> str | None:
    for pattern, target in LANDING_RULES:
        if pattern.match(intent):
            return target
    return None


def canonical_target_for_intent(intent: str) -> str:
    """Return site path (absolute path from root) for this intent."""
    landing = landing_target(intent)
    if landing:
        return landing
    kw = preferred_keyword(intent)
    slug = matrix_slug_for_keyword(kw)
    return f"/blog/{slug}.html"


def redirect_html(target_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>กำลังเปลี่ยนเส้นทาง… | Sangkan Clean</title>
  <link rel="canonical" href="{target_url}">
  <meta http-equiv="refresh" content="0;url={target_url}">
  <meta name="robots" content="noindex, follow">
  <script>location.replace({json.dumps(target_url)});</script>
</head>
<body>
  <p>กำลังพาไปยังหน้าหลักของบริการนี้: <a href="{target_url}">{target_url}</a></p>
</body>
</html>
"""


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_redirect_plan(posts: list[dict]) -> dict:
    """
    Group matrix posts by normalized intent.
    Keep the best post per intent (prefer matching preferred slug / higher volume proxy).
    Editorial (non-matrix) posts are kept as-is.
    """
    keepers: dict[str, dict] = {}
    losers: list[dict] = []
    editorial: list[dict] = []

    for post in posts:
        slug = post.get("slug") or ""
        if not slug.endswith(MATRIX_SUFFIX):
            editorial.append(post)
            continue

        kw = keyword_from_matrix_slug(slug) or keyword_from_title(post.get("title", ""))
        intent = normalize_intent(kw)
        target_path = canonical_target_for_intent(intent)
        preferred_slug = (
            None
            if target_path.startswith("/landing-")
            else Path(target_path).stem
        )

        score = 0
        if preferred_slug and slug == preferred_slug:
            score += 100
        # Prefer pages whose title keyword already equals preferred keyword
        if preferred_keyword(intent) in (kw, kw.replace(" ", "")):
            score += 20
        # Prefer longer content
        score += min(len(post.get("content") or ""), 5000) / 5000
        # Prefer Thai บิ๊กคลีนนิ่ง over leftover EN forms
        if "big-cleaning" in slug.lower() or "bigcleaning" in slug.lower():
            score -= 50

        candidate = {
            "post": post,
            "intent": intent,
            "keyword": kw,
            "slug": slug,
            "target_path": target_path,
            "score": score,
        }

        existing = keepers.get(intent)
        if existing is None or candidate["score"] > existing["score"]:
            if existing is not None:
                losers.append(existing)
            keepers[intent] = candidate
        else:
            losers.append(candidate)

    # If keeper redirects to a landing, the keeper itself is also a loser page
    final_keepers = []
    for intent, item in keepers.items():
        if item["target_path"].startswith("/landing-"):
            losers.append(item)
        else:
            final_keepers.append(item["post"])

    redirects = []
    seen_from = set()
    for item in losers:
        from_slug = item["slug"]
        if from_slug in seen_from:
            continue
        seen_from.add(from_slug)
        target = item["target_path"]
        # Don't redirect a page to itself
        if target == f"/blog/{from_slug}.html":
            continue
        redirects.append(
            {
                "from": f"/blog/{from_slug}.html",
                "to": target,
                "intent": item["intent"],
                "reason": "cannibalization",
            }
        )

    kept_posts = editorial + final_keepers
    # Stable-ish order: editorial first (by original date), then matrix by title
    kept_posts.sort(key=lambda p: (0 if not (p.get("slug") or "").endswith(MATRIX_SUFFIX) else 1, p.get("title", "")))

    return {
        "kept_posts": kept_posts,
        "redirects": redirects,
        "stats": {
            "original": len(posts),
            "kept": len(kept_posts),
            "redirects": len(redirects),
            "intents": len(keepers),
        },
    }


def dedupe_keywords(keywords: list[dict]) -> list[dict]:
    best: dict[str, dict] = {}
    for entry in keywords:
        kw = entry.get("keyword", "").strip()
        if not kw:
            continue
        intent = normalize_intent(kw)
        # Drop keywords that resolve to landings (served by landing pages)
        if landing_target(intent):
            continue
        volume = int(entry.get("search_volume") or 0)
        preferred = preferred_keyword(intent)
        prev = best.get(intent)
        # Prefer exact preferred keyword form, then higher volume
        score = volume
        if re.sub(r"\s+", "", kw) == preferred:
            score += 1_000_000
        if "Big Cleaning" in kw or "big cleaning" in kw.lower():
            score -= 100_000
        if prev is None or score > prev["_score"]:
            best[intent] = {
                "keyword": preferred,
                "search_volume": max(volume, int(prev["search_volume"]) if prev else 0),
                "_score": score,
            }
    out = [{"keyword": v["keyword"], "search_volume": v["search_volume"]} for v in best.values()]
    out.sort(key=lambda x: (-x["search_volume"], x["keyword"]))
    return out


def is_redirect_stub(path: Path) -> bool:
    """True if file is already a soft-redirect stub (do not copy as content)."""
    if not path.is_file():
        return False
    head = path.read_text(encoding="utf-8", errors="ignore")[:2500].lower()
    return 'http-equiv="refresh"' in head or "location.replace" in head


def write_redirect_files(redirects: list[dict]) -> int:
    """Write GH Pages–compatible HTML redirect stubs (+ optional _redirects for proxies).

    If the canonical target file is missing but the source still has real content
    (not already a stub), copy source → target first so we never 404.
    """
    blog_dir = ROOT / "blog"
    blog_dir.mkdir(exist_ok=True)
    written = 0
    for rule in redirects:
        from_path = rule["from"]  # /blog/slug.html
        to_path = rule["to"]
        from_file = ROOT / from_path.lstrip("/")
        to_file = ROOT / to_path.lstrip("/")
        target_url = SITE_URL + to_path

        if from_file.is_file() and not to_file.is_file() and not is_redirect_stub(from_file):
            to_file.parent.mkdir(parents=True, exist_ok=True)
            to_file.write_text(from_file.read_text(encoding="utf-8"), encoding="utf-8")

        from_file.parent.mkdir(parents=True, exist_ok=True)
        from_file.write_text(redirect_html(target_url), encoding="utf-8")
        written += 1

    # Cloudflare / Netlify style redirects (ignored by plain GH Pages, useful if proxy added)
    lines = ["# Auto-generated SEO cannibalization redirects", ""]
    for rule in redirects:
        lines.append(f"{rule['from']}  {rule['to']}  301")
    (ROOT / "_redirects").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return written


def apply(write_files: bool = True) -> dict:
    posts_path = ROOT / "posts.json"
    keywords_path = ROOT / "seo" / "keywords.json"
    redirects_path = ROOT / "seo" / "redirects.json"

    posts = load_json(posts_path)
    plan = build_redirect_plan(posts)

    if write_files:
        save_json(posts_path, plan["kept_posts"])
        save_json(redirects_path, plan["redirects"])
        if keywords_path.exists():
            save_json(keywords_path, dedupe_keywords(load_json(keywords_path)))
        written = write_redirect_files(plan["redirects"])
        plan["stats"]["redirect_files"] = written

    return plan


if __name__ == "__main__":
    result = apply(write_files=True)
    print(json.dumps(result["stats"], ensure_ascii=False, indent=2))
    print(f"Redirect rules: {len(result['redirects'])}")
