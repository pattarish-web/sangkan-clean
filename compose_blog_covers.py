# -*- coding: utf-8 -*-
"""Build Gen-Z blog covers: unique text overlays, background reused max 3 times."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from site_config import SITE_URL

ROOT = Path(__file__).resolve().parent
BG_DIR = ROOT / "images" / "blog" / "bg"
COVER_DIR = ROOT / "images" / "blog" / "covers"
FONTS = ROOT / "marketing" / "ads-office-ondemand" / "fonts"
MAX_PER_BG = 3
TEXT_MAX_W = 520

TEAL = (13, 148, 136)
CORAL = (251, 113, 133)
DARK = (15, 23, 42)
WHITE = (255, 255, 255)
SOFT = (241, 245, 249)
YELLOW = (250, 204, 21)

# Thai marks that must stay attached to the previous consonant
_THAI_FOLLOW = set("่้๊๋์ิีึืุู็ํัำฺ")

VENUE_ORDER = [
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
    (("คอนโด",), "home"),
    (("ออฟฟิศ", "สำนักงาน", "อาคาร"), "office"),
]

# Thai tokens longest-first — wrap only between these units (never mid-word)
_WRAP_TOKENS = sorted(
    [
        "ห้างสรรพสินค้า",
        "มหาวิทยาลัย",
        "โรงพยาบาล",
        "ทำความสะอาด",
        "บิ๊กคลีนนิ่ง",
        "Big Cleaning",
        "เคลียร์พื้นที่",
        "หลังก่อสร้าง",
        "แม่บ้าน",
        "โชว์รูม",
        "รีสอร์ท",
        "โรงแรม",
        "โรงงาน",
        "โกดัง",
        "คลินิก",
        "โรงเรียน",
        "ออฟฟิศ",
        "สำนักงาน",
        "ฟิตเนส",
        "คอนโด",
        "ตึกสูง",
        "ศูนย์การค้า",
        "ร้านอาหาร",
        "คาเฟ่",
        "จ้าง",
        "หา",
    ],
    key=len,
    reverse=True,
)

# Prefer same family before failing (never jump to unrelated venues like factory).
VENUE_FALLBACK = {
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


def venue_of(title: str) -> str:
    for keys, venue in VENUE_ORDER:
        if any(k in title for k in keys):
            return venue
    # "บ้าน" but not inside "แม่บ้าน"
    if re.search(r"(?<!แม่)บ้าน", title):
        return "home"
    return "office"


def clean_headline(title: str) -> str:
    t = re.sub(r"\s*\|.*$", "", title).strip()
    t = t.replace("ระดับมืออาชีพ", "").strip()
    t = re.sub(r"^บริการ\s*", "", t).strip()
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _text_w(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.ImageFont) -> int:
    bb = draw.textbbox((0, 0), text, font=f)
    return bb[2] - bb[0]


def _tokenize_headline(text: str) -> list[str]:
    """Split into known service tokens + remaining grapheme clusters."""
    parts: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == " ":
            parts.append(" ")
            i += 1
            continue
        matched = False
        for tok in _WRAP_TOKENS:
            if text.startswith(tok, i):
                parts.append(tok)
                i += len(tok)
                matched = True
                break
        if matched:
            continue
        j = i + 1
        while j < n and text[j] in _THAI_FOLLOW:
            j += 1
        parts.append(text[i:j])
        i = j
    return parts


def wrap_headline(title: str, draw: ImageDraw.ImageDraw, f: ImageFont.ImageFont, max_w: int = TEXT_MAX_W) -> list[str]:
    """Wrap on token boundaries only — never split Thai words mid-syllable."""
    t = clean_headline(title)
    if not t:
        return [""]
    if _text_w(draw, t, f) <= max_w:
        return [t]

    tokens = _tokenize_headline(t)
    lines: list[str] = []
    cur = ""
    for tok in tokens:
        if tok == " " and not cur:
            continue
        trial = (cur + tok) if cur else tok.lstrip()
        if cur and _text_w(draw, trial, f) > max_w:
            lines.append(cur.strip())
            cur = tok.lstrip()
            if len(lines) >= 3:
                break
        else:
            cur = trial
    if cur.strip() and len(lines) < 3:
        lines.append(cur.strip())
    elif cur.strip() and lines:
        # Overflow: shrink by appending to last line (caller should pick smaller font)
        lines[-1] = (lines[-1] + cur.strip())
    return lines or [t]


def font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = {
        "bold": "Prompt-Bold.ttf",
        "semibold": "Prompt-SemiBold.ttf",
        "medium": "Prompt-Medium.ttf",
        "regular": "Prompt-Regular.ttf",
    }
    p = FONTS / names.get(weight, "Prompt-Bold.ttf")
    if p.exists():
        return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def cover_fit(path: Path, size=(1080, 1080)) -> Image.Image:
    img = Image.open(path).convert("RGB")
    tw, th = size
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def left_wash(img: Image.Image) -> Image.Image:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for x in range(0, int(w * 0.55)):
        t = 1 - (x / (w * 0.55))
        a = int(170 * (t**1.35))
        d.line([(x, 0), (x, h)], fill=(15, 23, 42, a))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def ink(draw, xy, text, f, fill=WHITE):
    x, y = xy
    draw.text((x + 1, y + 2), text, font=f, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=f, fill=fill)


def compose(bg_path: Path, title: str, chip: str) -> Image.Image:
    img = left_wash(cover_fit(bg_path))
    img = ImageEnhance.Color(img).enhance(1.05)
    draw = ImageDraw.Draw(img)
    ink(draw, (48, 48), "Sangkan Clean", font(28, "semibold"), TEAL)
    draw.rounded_rectangle([48, 84, 128, 90], radius=3, fill=CORAL)

    cf = font(22, "semibold")
    bb = draw.textbbox((0, 0), chip, font=cf)
    cw, ch = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle([48, 110, 48 + cw + 28, 110 + ch + 16], radius=18, fill=CORAL)
    draw.text((48 + 14, 110 + 6), chip, font=cf, fill=DARK)

    # Prefer largest font that fits on 1 line; else best 2-line token wrap
    fsize = 34
    lines = [clean_headline(title)]
    one_line = None
    multi = None
    for size in (56, 48, 44, 40, 36, 32, 28):
        f = font(size, "bold")
        trial = wrap_headline(title, draw, f, TEXT_MAX_W)
        if len(trial) == 1 and _text_w(draw, trial[0], f) <= TEXT_MAX_W:
            one_line = (size, trial)
            break
        if multi is None and 1 < len(trial) <= 2 and all(_text_w(draw, ln, f) <= TEXT_MAX_W for ln in trial):
            multi = (size, trial)
    if one_line:
        fsize, lines = one_line
    elif multi:
        fsize, lines = multi
    else:
        f = font(28, "bold")
        fsize, lines = 28, wrap_headline(title, draw, f, TEXT_MAX_W)

    y = 220
    f = font(fsize, "bold")
    for line in lines[:3]:
        ink(draw, (48, y), line, f, WHITE)
        y += int(fsize * 1.25)

    y += 12
    ink(draw, (48, y), "ทีมมืออาชีพ · สั่งได้ดั่งใจ", font(22, "medium"), SOFT)
    y += 48
    cta = "ทัก LINE @sangkanclean"
    cf2 = font(24, "bold")
    bb = draw.textbbox((0, 0), cta, font=cf2)
    cw, ch = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle([48, y, 48 + cw + 40, y + ch + 22], radius=26, fill=TEAL)
    draw.text((48 + 20, y + 9), cta, font=cf2, fill=WHITE)
    draw.ellipse([960, 80, 1010, 130], fill=YELLOW)
    return img


def list_backgrounds() -> list[Path]:
    """Only numbered venue files: bg-{venue}-NN.jpg (skip legacy bg-factory.jpg)."""
    BG_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(BG_DIR.glob("bg-*-*.jpg")) + sorted(BG_DIR.glob("bg-*-*.png"))
    return files


def bg_venue(path: Path) -> str:
    m = re.match(r"bg-([a-z]+)-\d+", path.stem)
    return m.group(1) if m else "office"


def assign_bgs(posts: list[dict], bgs: list[Path]) -> dict[str, Path]:
    """Map slug -> bg path; same venue first, then related venues only."""
    if not bgs:
        raise SystemExit(f"No backgrounds in {BG_DIR}. Generate bg-*-NN.jpg first.")

    by_venue: dict[str, list[Path]] = defaultdict(list)
    for p in bgs:
        by_venue[bg_venue(p)].append(p)

    usage: dict[Path, int] = {p: 0 for p in bgs}
    mapping: dict[str, Path] = {}

    def pick(venue: str) -> Path:
        order = [venue] + [v for v in VENUE_FALLBACK.get(venue, []) if v != venue]
        # Pass 1: under MAX within preferred venues
        for v in order:
            for p in by_venue.get(v, []):
                if usage[p] < MAX_PER_BG:
                    usage[p] += 1
                    return p
        # Pass 2: soft over-reuse on exact venue only (keep visual theme)
        pool = by_venue.get(venue) or []
        for v in order[1:]:
            pool = pool or by_venue.get(v) or []
        if pool:
            p = min(pool, key=lambda x: usage[x])
            usage[p] += 1
            return p
        raise SystemExit(f"No backgrounds available for venue={venue}")

    for post in posts:
        venue = venue_of(post.get("title", ""))
        mapping[post["slug"]] = pick(venue)
    return mapping


def chip_for(title: str) -> str:
    if "มหาวิทยาลัย" in title:
        return "มหาวิทยาลัย"
    if "รีสอร์ท" in title:
        return "รีสอร์ท"
    if "โรงพยาบาล" in title:
        return "โรงพยาบาล"
    v = venue_of(title)
    labels = {
        "factory": "โรงงาน",
        "warehouse": "โกดัง",
        "hotel": "โรงแรม",
        "hospital": "คลินิก",
        "school": "โรงเรียน",
        "mall": "ห้าง/ศูนย์ฯ",
        "restaurant": "คาเฟ่/ร้านอาหาร",
        "showroom": "โชว์รูม",
        "highrise": "ตึกสูง",
        "gym": "ฟิตเนส",
        "home": "บ้าน/คอนโด",
        "office": "ออฟฟิศ",
    }
    return labels.get(v, "บริการ")


def main():
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    with open(ROOT / "posts.json", encoding="utf-8") as f:
        posts = json.load(f)

    bgs = list_backgrounds()
    mapping = assign_bgs(posts, bgs)
    today = date.today().isoformat()
    counts: dict[str, int] = defaultdict(int)
    mismatches = 0

    for i, post in enumerate(posts):
        slug = post["slug"]
        bg = mapping[slug]
        counts[bg.name] += 1
        need = venue_of(post.get("title", ""))
        got = bg_venue(bg)
        if need != got and got not in VENUE_FALLBACK.get(need, []):
            mismatches += 1
        out = COVER_DIR / f"c{i:03d}.jpg"
        img = compose(bg, post.get("title", ""), chip_for(post.get("title", "")))
        img.save(out, "JPEG", quality=85, optimize=True)
        rel = out.relative_to(ROOT).as_posix()
        post["image"] = f"{SITE_URL}/{rel}"
        post["dateModified"] = today

    with open(ROOT / "posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(
        f"covers={len(posts)} backgrounds_used={len(counts)} "
        f"max_reuse={max(counts.values())} hard_mismatches={mismatches}"
    )


if __name__ == "__main__":
    main()
