"""Daily social content orchestrator — image + short video mix."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
for p in (str(ROOT), str(REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)

from compose_image import save_feed, save_stories  # noqa: E402
from creative_standard import (  # noqa: E402
    SUBLINE_MAX,
    THAI_TONE_RULES,
    build_background_prompt,
    clip_subline,
)
from render_video import (  # noqa: E402
    has_ffmpeg,
    render_feed_clip,
    render_stories_clip,
)
from topics import pick_topic  # noqa: E402

LOG_PATH = ROOT / "log.json"
OUT_DIR = ROOT / "out"

SITE = "https://www.sangkanclean.com"
LINE_OA = "@sangkanclean"
PHONE = "063-686-5134"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _channels() -> set[str]:
    raw = os.environ.get("CHANNELS", "facebook,instagram,tiktok,line").strip()
    return {c.strip().lower() for c in raw.split(",") if c.strip()}


def _load_log() -> dict:
    if not LOG_PATH.exists():
        return {"last_topic": None, "posts": []}
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_topic": None, "posts": []}


def _save_log(data: dict) -> None:
    LOG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _fallback_captions(topic: dict) -> dict:
    hl = topic["headline"]
    angle = topic["angle"]
    cta = f"ทัก LINE {LINE_OA} หรือดูรายละเอียดที่ {SITE}"
    return {
        "fb_ig": (
            f"{hl}\n\n{angle}\n\n"
            f"Sangkan Clean — คลีนออฟฟิศให้ทีมวัยใหม่ เอเจนซี่ และเทค\n"
            f"{cta}\nโทร {PHONE}"
        ),
        "tiktok": f"{hl}\n{angle}\nLINE {LINE_OA}",
        "line": f"{hl}\n\n{angle}\n\nทักไลน์ {LINE_OA} ได้เลย",
        "image_subline": clip_subline(angle),
        "hashtags": ["#SangkanClean", "#แม่บ้านออฟฟิศ", "#BigCleaning"],
    }


def _generate_captions(topic: dict) -> dict:
    try:
        from gemini_api import call_gemini_json_rotate, get_api_keys
    except ImportError:
        return _fallback_captions(topic)

    keys = get_api_keys()
    if not keys:
        print("No GEMINI_API_KEY — using fallback captions")
        return _fallback_captions(topic)

    print(f"Captions: rotating across {len(keys)} Gemini API key(s)")
    prompt = f"""คุณเขียนคอนเทนต์โซเชียลภาษาไทยให้แบรนด์ Sangkan Clean เท่านั้น
{THAI_TONE_RULES}

หัวข้อวันนี้: {topic["label"]}
มุม: {topic["angle"]}
หัวข้อกราฟิก: {topic["headline"]}
CTA ที่ต้องมี: LINE {LINE_OA} และเว็บ {SITE}
โทรศัพท์ (ใส่ได้ถ้าเหมาะสม): {PHONE}

คืน JSON เท่านั้น:
{{
  "fb_ig": "แคปชัน Facebook/Instagram ภาษาไทย 60-140 คำ มี CTA โทนคุยเพื่อนทำงาน ไม่เป็นทางการ",
  "tiktok": "แคปชัน TikTok สั้น 30-70 คำ โทนเดียวกัน",
  "line": "ข้อความ LINE broadcast 40-100 คำ โทนเดียวกัน ห้ามขึ้นต้นด้วย เรียน",
  "image_subline": "ประโยครองใต้หัวข้อบนกราฟิก ภาษาไทย สั้นมาก ไม่เกิน {SUBLINE_MAX} ตัวอักษร",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
}}
"""
    data = call_gemini_json_rotate(keys, prompt, key_label_prefix="social-bot")
    if not data or not isinstance(data, dict):
        print("Gemini failed on all keys — using fallback captions")
        return _fallback_captions(topic)

    base = _fallback_captions(topic)
    for key in ("fb_ig", "tiktok", "line", "image_subline", "hashtags"):
        if key in data and data[key]:
            base[key] = data[key]
    if isinstance(base.get("image_subline"), str):
        base["image_subline"] = clip_subline(base["image_subline"])
    for key in ("fb_ig", "tiktok", "line", "image_subline"):
        if isinstance(base.get(key), str):
            base[key] = (
                base[key]
                .replace("สั่งการคลีน", "Sangkan Clean")
                .replace("สังการคลีน", "Sangkan Clean")
            )
    return base


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


# Scene one-liners only — shared Instagram lifestyle brief is in creative_standard.
SCENE_BY_TOPIC: dict[str, str] = {
    "office_ondemand": (
        "open Bangkok coworking floor, young professionals working casually at desks, "
        "floor-to-ceiling windows, indoor plants"
    ),
    "agency_focus": (
        "creative agency studio with soft moodboard wall, tidy open plan, "
        "casual-smart team collaborating in soft focus"
    ),
    "tech_team": (
        "bright startup office with clean desks and monitors, "
        "energetic but uncluttered, glass meeting room soft background"
    ),
    "big_cleaning": (
        "freshly deep-cleaned modern office after hours, polished floors catching daylight, "
        "subtle cleaning tools softly blurred in background"
    ),
    "maid_backup": (
        "bright clean office interior with a discreet professional cleaning cart "
        "softly out of focus — not a stiff utility room"
    ),
    "service_area": (
        "airy Bangkok office interior with soft city light through windows, "
        "clean desks and plants in foreground"
    ),
    "price_pack": (
        "premium small home-office / boutique agency desk lifestyle shot, "
        "notebook plant morning light, left third kept simple"
    ),
    "affiliate": (
        "two young colleagues chatting casually in a café-style office lounge, "
        "friendly daylight, clean modern space"
    ),
    "after_construction": (
        "newly finished bright commercial space being detailed, "
        "dust cleanup nearly done, airy unfinished-to-clean transition"
    ),
    "soft_cleaning": (
        "gentle daily tidy of a modern condo living area / soft surfaces, "
        "microfiber cloths subtle, calm natural light"
    ),
}


def _background_prompt(topic: dict) -> str:
    scene = SCENE_BY_TOPIC.get(topic["id"], "")
    return build_background_prompt(
        scene,
        topic_mood=str(topic.get("label", topic["id"])),
    )


# Same lifestyle photo pool as blog covers (Pillow overlay) — not genz/art ads.
STOCK_BG_DIR = REPO / "images" / "blog" / "bg"
VENUE_BY_TOPIC: dict[str, str] = {
    "office_ondemand": "office",
    "agency_focus": "office",
    "tech_team": "office",
    "big_cleaning": "office",
    "maid_backup": "office",
    "service_area": "office",
    "price_pack": "office",
    "affiliate": "office",
    "after_construction": "warehouse",
    "soft_cleaning": "home",
}

# Keyword → venue (same idea as compose_blog_covers.venue_of). First match wins.
VENUE_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("โรงงาน",), "factory"),
    (("โกดัง",), "warehouse"),
    (("โรงแรม", "รีสอร์ท"), "hotel"),
    (("โรงพยาบาล", "คลินิก"), "hospital"),
    (("โรงเรียน", "มหาวิทยาลัย"), "school"),
    (("ห้าง", "ศูนย์การค้า"), "mall"),
    (("ร้านอาหาร", "คาเฟ่"), "restaurant"),
    (("โชว์รูม",), "showroom"),
    (("ตึกสูง",), "highrise"),
    (("ฟิตเนส",), "gym"),
    (("คอนโด", "บ้าน", "โฮม"), "home"),
    (("ออฟฟิศ", "สำนักงาน", "อาคาร", "เอเจนซี่", "สตาร์ทอัพ", "tech"), "office"),
    (("ก่อสร้าง", "ฝุ่นปูน", "คราบสี"), "warehouse"),
]

VENUE_FALLBACK: dict[str, list[str]] = {
    "school": ["office", "home"],
    "mall": ["showroom", "office"],
    "hospital": ["office"],
    "restaurant": ["mall", "office"],
    "home": ["highrise", "office"],
    "hotel": ["home", "office"],
    "warehouse": ["factory", "office"],
    "factory": ["warehouse", "office"],
    "showroom": ["mall", "office"],
    "highrise": ["office", "home"],
    "gym": ["office"],
    "office": ["home"],
}


def _bg_venue(path: Path) -> str:
    m = re.match(r"bg-([a-z]+)-\d+", path.stem)
    return m.group(1) if m else ""


def _venue_from_text(text: str) -> str | None:
    blob = (text or "").lower()
    for keys, venue in VENUE_KEYWORDS:
        if any(k.lower() in blob for k in keys):
            return venue
    return None


def _expected_venue(topic: dict, captions: dict | None = None) -> str:
    """Infer venue from copy first, then topic default — so bg matches the post."""
    parts = [
        str(topic.get("headline", "")),
        str(topic.get("angle", "")),
        str(topic.get("label", "")),
    ]
    if captions:
        for key in ("fb_ig", "image_subline", "tiktok", "line"):
            if captions.get(key):
                parts.append(str(captions[key]))
    hit = _venue_from_text(" ".join(parts))
    if hit:
        return hit
    return VENUE_BY_TOPIC.get(topic["id"], "office")


def _venue_ok(need: str, got: str) -> bool:
    if not got:
        return False
    if need == got:
        return True
    return got in VENUE_FALLBACK.get(need, [])


def _list_stock_bgs(venue: str) -> list[Path]:
    """Numbered venue files only: bg-{venue}-NN.jpg (same rule as blog covers)."""
    if not STOCK_BG_DIR.is_dir():
        return []
    files = sorted(STOCK_BG_DIR.glob(f"bg-{venue}-*.jpg"))
    files += sorted(STOCK_BG_DIR.glob(f"bg-{venue}-*.png"))
    return files


def _stock_background(topic: dict, venue: str | None = None) -> Path | None:
    """Pick a lifestyle photo matching the expected venue (+ related fallbacks)."""
    need = venue or _expected_venue(topic)
    order = [need] + [v for v in VENUE_FALLBACK.get(need, []) if v != need]
    pool: list[Path] = []
    for v in order:
        pool = _list_stock_bgs(v)
        if pool:
            need = v
            break
    if not pool:
        pool = _list_stock_bgs("office")
        need = "office"
    if not pool:
        return None
    seed = f"{_stamp()}:{topic['id']}:{need}"
    idx = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16) % len(pool)
    chosen = pool[idx]
    print(f"Stock venue need={need} file={chosen.name}")
    return chosen


def _gemini_background(topic: dict, out_dir: Path) -> Path | None:
    """Optional Gemini image gen (often 429 on free tier)."""
    try:
        from gemini_api import call_gemini_image_rotate, get_api_keys
    except ImportError:
        return None

    keys = get_api_keys()
    if not keys:
        return None

    print(f"Background: trying Gemini across {len(keys)} key(s)")
    raw = call_gemini_image_rotate(
        keys, _background_prompt(topic), key_label_prefix="social-bot-bg"
    )
    if not raw:
        return None

    ext = "png" if raw[:8].startswith(b"\x89PNG") else "jpg"
    path = out_dir / f"bg.{ext}"
    path.write_bytes(raw)
    print(f"Gemini background saved -> {path.name} ({len(raw)} bytes)")
    return path


def _resolve_background(
    topic: dict,
    out_dir: Path,
    captions: dict | None = None,
    force_venue: str | None = None,
) -> tuple[Path | None, dict]:
    """Return (bg_path, meta) with venue relevance fields."""
    need = force_venue or _expected_venue(topic, captions)
    meta = {
        "venue_need": need,
        "venue_got": "",
        "bg_source": "",
        "relevance_ok": False,
    }

    if _env_bool("SOCIAL_GEMINI_BG", default=False) and not force_venue:
        gem = _gemini_background(topic, out_dir)
        if gem:
            # Gemini has no venue tag — treat as ok but mark source
            meta.update(
                {
                    "venue_got": "gemini",
                    "bg_source": gem.name,
                    "relevance_ok": True,
                }
            )
            return gem, meta
        print("Gemini bg unavailable — falling back to stock lifestyle photo")

    stock = _stock_background(topic, venue=need)
    if stock and stock.exists():
        got = _bg_venue(stock) or need
        ok = _venue_ok(need, got)
        dest = out_dir / f"bg{stock.suffix.lower()}"
        shutil.copy2(stock, dest)
        meta.update(
            {
                "venue_got": got,
                "bg_source": stock.name,
                "relevance_ok": ok,
            }
        )
        print(
            f"Stock lifestyle bg -> {stock.name} "
            f"(need={need} got={got} ok={ok})"
        )
        if not ok:
            print(f"RELEVANCE WARN: bg {stock.name} does not match venue {need}")
        return dest, meta

    print("No stock bg found — gradient fallback")
    return None, meta


def build_assets(
    topic: dict,
    captions: dict,
    *,
    force_venue: str | None = None,
) -> dict[str, str]:
    """Create PNG (+ MP4 as needed). Returns relative paths under social-bot/."""
    day = _stamp()
    out = OUT_DIR / day
    out.mkdir(parents=True, exist_ok=True)

    headline = topic["headline"]
    sub = clip_subline(str(captions.get("image_subline") or topic["angle"]))

    bg_path, bg_meta = _resolve_background(
        topic, out, captions=captions, force_venue=force_venue
    )

    feed_png = out / "feed.png"
    stories_png = out / "stories.png"
    save_feed(headline, sub, feed_png, topic_id=topic["id"], background=bg_path)
    save_stories(headline, sub, stories_png, topic_id=topic["id"], background=bg_path)

    assets: dict[str, str] = {
        "feed_png": str(feed_png.relative_to(ROOT)).replace("\\", "/"),
        "stories_png": str(stories_png.relative_to(ROOT)).replace("\\", "/"),
        "venue_need": bg_meta.get("venue_need", ""),
        "venue_got": bg_meta.get("venue_got", ""),
        "bg_source": bg_meta.get("bg_source", ""),
        "relevance_ok": "1" if bg_meta.get("relevance_ok") else "0",
    }
    if bg_path and bg_path.exists():
        assets["bg"] = str(bg_path.relative_to(ROOT)).replace("\\", "/")

    fmt = topic.get("format", "image")
    need_stories_video = True  # TikTok always
    need_feed_video = fmt == "video"

    if (need_stories_video or need_feed_video) and not has_ffmpeg():
        print("WARNING: ffmpeg not found — skipping video render")
        return assets

    if need_stories_video:
        stories_mp4 = out / "stories.mp4"
        render_stories_clip(stories_png, stories_mp4, duration=10.0)
        assets["stories_mp4"] = str(stories_mp4.relative_to(ROOT)).replace("\\", "/")

    if need_feed_video:
        feed_mp4 = out / "feed.mp4"
        render_feed_clip(feed_png, feed_mp4, duration=10.0)
        assets["feed_mp4"] = str(feed_mp4.relative_to(ROOT)).replace("\\", "/")

    return assets


def _ensure_bg_relevance(topic: dict, captions: dict, assets: dict[str, str]) -> dict[str, str]:
    """Before publish: if stock venue mismatches copy, rebuild with correct venue."""
    need = _expected_venue(topic, captions)
    got = str(assets.get("venue_got") or "")
    if assets.get("relevance_ok") == "1" and _venue_ok(need, got):
        print(f"Relevance OK: venue={got} (need={need})")
        return assets

    if got == "gemini":
        return assets

    print(f"Relevance check FAIL: need={need} got={got or 'none'} — rebuilding assets")
    rebuilt = build_assets(topic, captions, force_venue=need)
    if rebuilt.get("relevance_ok") != "1":
        # Last attempt: office is safest for most social topics
        if need != "office":
            print("Retry relevance with office venue")
            rebuilt = build_assets(topic, captions, force_venue="office")
    return rebuilt


def publish_all(
    topic: dict,
    captions: dict,
    assets: dict[str, str],
    channels: set[str],
    dry_run: bool,
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    fmt = topic.get("format", "image")
    tags = captions.get("hashtags") or []
    tag_str = " ".join(tags) if isinstance(tags, list) else str(tags)

    fb_caption = f"{captions['fb_ig']}\n\n{tag_str}".strip()
    tt_caption = f"{captions['tiktok']}\n\n{tag_str}".strip()

    def abs_asset(key: str) -> Path | None:
        rel = assets.get(key)
        if not rel:
            return None
        return ROOT / rel

    if "facebook" in channels:
        from publish_meta import publish_facebook

        results["facebook"] = publish_facebook(
            caption=fb_caption,
            image_path=abs_asset("feed_png"),
            video_path=abs_asset("feed_mp4") if fmt == "video" else None,
            dry_run=dry_run,
        )

    if "instagram" in channels:
        from publish_meta import publish_instagram

        results["instagram"] = publish_instagram(
            caption=fb_caption,
            image_path=abs_asset("feed_png"),
            video_path=abs_asset("stories_mp4") if fmt == "video" else None,
            use_reels=fmt == "video",
            dry_run=dry_run,
        )

    if "tiktok" in channels:
        from publish_tiktok import publish_tiktok

        results["tiktok"] = publish_tiktok(
            caption=tt_caption,
            video_path=abs_asset("stories_mp4"),
            dry_run=dry_run,
        )

    if "line" in channels:
        from publish_line import publish_line

        results["line"] = publish_line(
            text=captions["line"],
            image_path=abs_asset("feed_png"),
            headline=topic["headline"],
            dry_run=dry_run,
        )

    return results


def main() -> int:
    dry_run = _env_bool("DRY_RUN", default=False)
    channels = _channels()
    log = _load_log()
    topic = pick_topic(log.get("last_topic"))
    fmt = topic.get("format", "image")

    print(f"Topic: {topic['id']} ({fmt}) dry_run={dry_run} channels={sorted(channels)}")

    captions = _generate_captions(topic)
    assets = build_assets(topic, captions)
    assets = _ensure_bg_relevance(topic, captions, assets)
    print("Assets:", json.dumps(assets, ensure_ascii=False))

    if assets.get("relevance_ok") != "1" and assets.get("venue_got") != "gemini":
        print(
            "ABORT publish: image venue does not match post copy "
            f"(need={assets.get('venue_need')} got={assets.get('venue_got')} "
            f"source={assets.get('bg_source')})"
        )
        # Still write log for debugging, but do not publish.
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "topic_id": topic["id"],
            "format": fmt,
            "dry_run": dry_run,
            "assets": assets,
            "captions": {
                "fb_ig": captions.get("fb_ig", "")[:200],
                "tiktok": captions.get("tiktok", "")[:120],
                "line": captions.get("line", "")[:120],
            },
            "results": {"skipped": {"ok": False, "reason": "bg_relevance"}},
        }
        posts = log.get("posts") or []
        posts.append(entry)
        log["posts"] = posts[-60:]
        log["last_topic"] = topic["id"]
        _save_log(log)
        return 1

    results = publish_all(topic, captions, assets, channels, dry_run)

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "topic_id": topic["id"],
        "format": fmt,
        "dry_run": dry_run,
        "assets": assets,
        "captions": {
            "fb_ig": captions.get("fb_ig", "")[:200],
            "tiktok": captions.get("tiktok", "")[:120],
            "line": captions.get("line", "")[:120],
        },
        "results": results,
    }
    posts = log.get("posts") or []
    posts.append(entry)
    log["posts"] = posts[-60:]  # keep last ~2 months
    log["last_topic"] = topic["id"]
    _save_log(log)

    # Also dump full captions for dry-run review
    if dry_run:
        day = _stamp()
        cap_path = OUT_DIR / day / "captions.json"
        cap_path.write_text(
            json.dumps(captions, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {cap_path}")

    print("Results:", json.dumps(results, ensure_ascii=False))
    failed = [
        name
        for name, res in results.items()
        if not res.get("ok") and not dry_run and res.get("skipped") is not True
    ]
    if failed:
        print("Publish failures:", failed)
        for name in failed:
            print(f"  {name}: {json.dumps(results.get(name), ensure_ascii=False)}")
        return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
