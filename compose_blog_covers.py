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

TEAL = (13, 148, 136)
CORAL = (251, 113, 133)
DARK = (15, 23, 42)
WHITE = (255, 255, 255)
SOFT = (241, 245, 249)
YELLOW = (250, 204, 21)

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
    (("คอนโด", "บ้าน"), "home"),
    (("ออฟฟิศ", "สำนักงาน", "อาคาร"), "office"),
]


def venue_of(title: str) -> str:
    for keys, venue in VENUE_ORDER:
        if any(k in title for k in keys):
            return venue
    return "office"


def headline_lines(title: str) -> list[str]:
    t = re.sub(r"\s*\|.*$", "", title).strip()
    t = t.replace("ระดับมืออาชีพ", "").strip()
    t = re.sub(r"^บริการ\s*", "", t).strip()
    # Prefer 2 short lines
    if len(t) <= 14:
        return [t]
    # Split near middle on space
    mid = len(t) // 2
    cut = t.rfind(" ", 0, mid + 4)
    if cut < 4:
        cut = t.find(" ", mid)
    if cut < 4:
        return [t[:16], t[16:32]] if len(t) > 16 else [t]
    return [t[:cut].strip(), t[cut:].strip()]


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

    # chip
    cf = font(22, "semibold")
    bb = draw.textbbox((0, 0), chip, font=cf)
    cw, ch = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle([48, 110, 48 + cw + 28, 110 + ch + 16], radius=18, fill=CORAL)
    draw.text((48 + 14, 110 + 6), chip, font=cf, fill=DARK)

    lines = headline_lines(title)
    y = 220
    for line in lines[:3]:
        fsize = 56 if len(line) < 12 else 44 if len(line) < 18 else 34
        f = font(fsize, "bold")
        ink(draw, (48, y), line, f, WHITE)
        y += int(fsize * 1.2)

    y += 12
    ink(draw, (48, y), "ทีมมืออาชีพ · สั่งได้ดั่งใจ", font(22, "medium"), SOFT)
    y += 48
    cta = "ทัก LINE @sangkanclean"
    cf2 = font(24, "bold")
    bb = draw.textbbox((0, 0), cta, font=cf2)
    cw, ch = bb[2] - bb[0], bb[3] - bb[1]
    draw.rounded_rectangle([48, y, 48 + cw + 40, y + ch + 22], radius=26, fill=TEAL)
    draw.text((48 + 20, y + 9), cta, font=cf2, fill=WHITE)
    # soft yellow accent chip
    draw.ellipse([960, 80, 1010, 130], fill=YELLOW)
    return img


def list_backgrounds() -> list[Path]:
    BG_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(BG_DIR.glob("bg-*.jpg")) + sorted(BG_DIR.glob("bg-*.png"))
    return files


def assign_bgs(posts: list[dict], bgs: list[Path]) -> dict[str, Path]:
    """Map slug -> bg path, max MAX_PER_BG per bg, prefer venue match in filename."""
    if not bgs:
        raise SystemExit(f"No backgrounds in {BG_DIR}. Generate bg-*.jpg first.")
    need = math.ceil(len(posts) / MAX_PER_BG)
    if len(bgs) < need:
        raise SystemExit(
            f"Need >= {need} backgrounds for {len(posts)} posts (max {MAX_PER_BG}/bg), have {len(bgs)}"
        )

    by_venue: dict[str, list[Path]] = defaultdict(list)
    for p in bgs:
        # bg-office-01.jpg → office
        m = re.match(r"bg-([a-z]+)", p.stem)
        key = m.group(1) if m else "office"
        by_venue[key].append(p)

    usage: dict[Path, int] = {p: 0 for p in bgs}
    mapping: dict[str, Path] = {}

    def pick(venue: str) -> Path:
        pool = list(by_venue.get(venue) or []) + list(bgs)
        for p in pool:
            if usage[p] < MAX_PER_BG:
                usage[p] += 1
                return p
        raise SystemExit("Ran out of background slots")

    for post in posts:
        venue = venue_of(post.get("title", ""))
        mapping[post["slug"]] = pick(venue)
    return mapping


def chip_for(title: str) -> str:
    v = venue_of(title)
    labels = {
        "factory": "โรงงาน",
        "warehouse": "โกดัง",
        "hotel": "โรงแรม",
        "hospital": "คลินิก/รพ.",
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

    for i, post in enumerate(posts):
        slug = post["slug"]
        bg = mapping[slug]
        counts[bg.name] += 1
        # short stable filename (avoid Windows path limits with Thai slugs)
        out = COVER_DIR / f"c{i:03d}.jpg"
        img = compose(bg, post.get("title", ""), chip_for(post.get("title", "")))
        img.save(out, "JPEG", quality=85, optimize=True)
        rel = out.relative_to(ROOT).as_posix()
        post["image"] = f"{SITE_URL}/{rel}"
        post["dateModified"] = today

    with open(ROOT / "posts.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"covers={len(posts)} backgrounds_used={len(counts)} max_reuse={max(counts.values())}")
    assert max(counts.values()) <= MAX_PER_BG


if __name__ == "__main__":
    main()
