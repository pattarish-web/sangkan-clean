"""Compose feed/stories graphics in genz / young-agency style.

Uses photo backgrounds from ads-office-ondemand/genz/art + Prompt Thai fonts.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parent
ADS = ROOT.parent / "ads-office-ondemand"
FONTS_DIR = ADS / "fonts"
ART_DIR = ADS / "genz" / "art"

TEAL = (13, 148, 136)
CORAL = (251, 113, 133)
DARK = (15, 23, 42)
WHITE = (255, 255, 255)
SOFT = (241, 245, 249)
INK = (15, 23, 42)
MUTED = (100, 116, 139)
YELLOW = (250, 204, 21)

FEED_SIZE = (1080, 1080)
STORIES_SIZE = (1080, 1920)

# topic_id → background art file
ART_BY_TOPIC: dict[str, str] = {
    "office_ondemand": "genz-A-cowork.png",
    "agency_focus": "genz-A-cowork.png",
    "tech_team": "genz-C-phone.png",
    "big_cleaning": "genz-D-morning.png",
    "maid_backup": "genz-E-friends.png",
    "service_area": "genz-A-cowork.png",
    "price_pack": "genz-B-flatlay.png",
    "affiliate": "genz-E-friends.png",
    "after_construction": "genz-D-morning.png",
    "soft_cleaning": "genz-B-flatlay.png",
}

CHIP_BY_TOPIC: dict[str, tuple[str, tuple[int, int, int]]] = {
    "office_ondemand": ("สำหรับทีมวัยใหม่", CORAL),
    "agency_focus": ("เอเจนซี่ / ครีเอทีฟ", CORAL),
    "tech_team": ("โปร่งใส 100%", YELLOW),
    "big_cleaning": ("Big Cleaning", CORAL),
    "maid_backup": ("มีคนสำรอง", YELLOW),
    "service_area": ("กรุงเทพฯ–ปริมณฑล", CORAL),
    "price_pack": ("แพ็คง่ายๆ", CORAL),
    "affiliate": ("ชวนเพื่อน = ได้ตังค์คืน", YELLOW),
    "after_construction": ("หลังก่อสร้าง", CORAL),
    "soft_cleaning": ("Soft Cleaning", YELLOW),
}

_PROMPT = {
    "bold": FONTS_DIR / "Prompt-Bold.ttf",
    "semibold": FONTS_DIR / "Prompt-SemiBold.ttf",
    "medium": FONTS_DIR / "Prompt-Medium.ttf",
    "regular": FONTS_DIR / "Prompt-Regular.ttf",
}


def _load(path: Path, size: int) -> ImageFont.ImageFont:
    if path.exists():
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def font(size: int, weight: str = "semibold") -> ImageFont.ImageFont:
    for key in (weight, "semibold", "bold", "medium", "regular"):
        if key in _PROMPT:
            return _load(_PROMPT[key], size)
    return ImageFont.load_default()


def text_wh(draw: ImageDraw.ImageDraw, text: str, fnt) -> tuple[int, int]:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0], b[3] - b[1]


def wrap_lines(draw, text: str, fnt, max_width: int) -> list[str]:
    words = text.replace("\n", " ").split()
    if not words:
        return []
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        tw, _ = text_wh(draw, trial, fnt)
        if tw <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def cover(path: Path, size: tuple[int, int]) -> Image.Image:
    img = Image.open(path).convert("RGB")
    tw, th = size
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def wash_bottom(img: Image.Image, start_ratio: float = 0.42) -> Image.Image:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    start = int(h * start_ratio)
    for y in range(start, h):
        t = (y - start) / max(h - start, 1)
        d.line([(0, y), (w, y)], fill=(15, 23, 42, int(200 * t**1.3)))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def ink(draw, xy, text, fnt, fill=WHITE, shadow: bool = True):
    x, y = xy
    if shadow:
        draw.text((x + 1, y + 2), text, font=fnt, fill=(0, 0, 0))
    draw.text((x, y), text, font=fnt, fill=fill)


def chip(draw, x, y, text, bg=CORAL, fg=DARK) -> int:
    fnt = font(24, "semibold")
    w, h = text_wh(draw, text, fnt)
    draw.rounded_rectangle([x, y, x + w + 36, y + h + 20], radius=22, fill=bg)
    draw.text((x + 18, y + 8), text, font=fnt, fill=fg)
    return y + h + 20


def cta(draw, x, y, text, bg=TEAL) -> int:
    fnt = font(28, "bold")
    w, h = text_wh(draw, text, fnt)
    draw.rounded_rectangle([x, y, x + w + 48, y + h + 28], radius=30, fill=bg)
    draw.text((x + 24, y + 12), text, font=fnt, fill=WHITE)
    return y + h + 28


def brand(draw, x: int = 40, y: int = 32, name: str = "Sangkan Clean"):
    ink(draw, (x, y), name, font(28, "semibold"), TEAL)
    draw.rounded_rectangle([x, y + 36, x + 72, y + 42], radius=3, fill=CORAL)


def _art_path(topic_id: str) -> Path:
    name = ART_BY_TOPIC.get(topic_id, "genz-A-cowork.png")
    path = ART_DIR / name
    if path.exists():
        return path
    # fallback: any available art
    for p in sorted(ART_DIR.glob("genz-*.png")):
        return p
    raise FileNotFoundError(
        f"Missing genz art under {ART_DIR} — commit marketing/ads-office-ondemand/genz/art/"
    )


def compose(
    headline: str,
    subline: str = "",
    *,
    size: tuple[int, int] = FEED_SIZE,
    topic_id: str = "office_ondemand",
    brand_name: str = "Sangkan Clean",
) -> Image.Image:
    w, h = size
    is_stories = h > w
    art = _art_path(topic_id)
    use_panel = topic_id == "price_pack" and not is_stories

    if use_panel:
        img = cover(art, size)
    else:
        img = wash_bottom(cover(art, size), 0.38 if is_stories else 0.42)

    draw = ImageDraw.Draw(img)
    brand(draw, name=brand_name)

    chip_text, chip_bg = CHIP_BY_TOPIC.get(topic_id, ("Sangkan Clean", CORAL))
    chip(draw, 40, 100, chip_text, chip_bg, DARK)

    if use_panel:
        panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle(
            [24, 150, int(w * 0.68), h - 28],
            radius=28,
            fill=(255, 255, 255, 240),
        )
        img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
        draw = ImageDraw.Draw(img)
        x, y = 48, 180
        head_f = font(40, "bold")
        for line in wrap_lines(draw, headline, head_f, int(w * 0.55))[:3]:
            ink(draw, (x, y), line, head_f, INK, shadow=False)
            y += 48
        if subline:
            y += 8
            sub_f = font(22, "medium")
            for line in wrap_lines(draw, subline, sub_f, int(w * 0.55))[:3]:
                ink(draw, (x, y), line, sub_f, MUTED, shadow=False)
                y += 32
        cta(draw, x, min(y + 28, h - 120), "ทัก LINE @sangkanclean", TEAL)
    else:
        max_w = int(w * (0.88 if is_stories else 0.78))
        y = int(h * (0.46 if is_stories else 0.42))
        head_f = font(64 if is_stories else 56, "bold")
        for line in wrap_lines(draw, headline, head_f, max_w)[:3]:
            ink(draw, (40, y), line, head_f, WHITE)
            y += 70 if is_stories else 64
        if subline:
            y += 8
            sub_f = font(26 if is_stories else 24, "medium")
            for line in wrap_lines(draw, subline, sub_f, max_w)[:2]:
                ink(draw, (40, y), line, sub_f, SOFT)
                y += 36
        cta(draw, 40, min(y + 24, h - 120), "ทัก LINE @sangkanclean")

    return ImageEnhance.Color(img).enhance(1.08)


def save_feed(
    headline: str,
    subline: str,
    path: Path,
    *,
    topic_id: str = "office_ondemand",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    compose(headline, subline, size=FEED_SIZE, topic_id=topic_id).save(
        path, "PNG", optimize=True
    )
    return path


def save_stories(
    headline: str,
    subline: str,
    path: Path,
    *,
    topic_id: str = "office_ondemand",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    compose(headline, subline, size=STORIES_SIZE, topic_id=topic_id).save(
        path, "PNG", optimize=True
    )
    return path
