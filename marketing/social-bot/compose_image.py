"""Compose feed/stories graphics in genz / young-agency layout style.

Layout reference only (brand, chip, headline, CTA, wash). Backgrounds are
passed in (typically Gemini-generated) — not stock from ads genz/art.
Fonts: Prompt Thai under ads-office-ondemand/fonts.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from creative_standard import TYPE  # noqa: E402

ADS = ROOT.parent / "ads-office-ondemand"
FONTS_DIR = ADS / "fonts"

TEAL = (13, 148, 136)
CORAL = (251, 113, 133)
DARK = (15, 23, 42)
WHITE = (255, 255, 255)
SOFT = (241, 245, 249)
INK = (15, 23, 42)
MUTED = (100, 116, 139)
YELLOW = (250, 204, 21)
MINT = (153, 246, 228)

FEED_SIZE = (1080, 1080)
STORIES_SIZE = (1080, 1920)

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


def cover_image(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    img = img.convert("RGB")
    tw, th = size
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def cover(path: Path, size: tuple[int, int]) -> Image.Image:
    return cover_image(Image.open(path), size)


def branded_gradient(size: tuple[int, int]) -> Image.Image:
    """Fallback canvas when Gemini background is unavailable (no genz art)."""
    w, h = size
    img = Image.new("RGB", size, WHITE)
    draw = ImageDraw.Draw(img)
    # Soft teal wash from top-right
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(255 * (1 - t * 0.15) + TEAL[0] * t * 0.12)
        g = int(255 * (1 - t * 0.12) + TEAL[1] * t * 0.18)
        b = int(255 * (1 - t * 0.1) + TEAL[2] * t * 0.2)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    # Diagonal mint / teal bands on the right (layout hint, not a photo)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.polygon(
        [(int(w * 0.55), 0), (w, 0), (w, int(h * 0.55)), (int(w * 0.35), h)],
        fill=(*TEAL, 90),
    )
    od.polygon(
        [(int(w * 0.75), 0), (w, 0), (w, int(h * 0.35)), (int(w * 0.55), h)],
        fill=(*MINT, 120),
    )
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


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
    fnt = font(TYPE["chip"], "semibold")
    w, h = text_wh(draw, text, fnt)
    draw.rounded_rectangle([x, y, x + w + 40, y + h + 24], radius=24, fill=bg)
    draw.text((x + 20, y + 10), text, font=fnt, fill=fg)
    return y + h + 24


def cta(draw, x, y, text, bg=TEAL) -> int:
    fnt = font(TYPE["cta"], "bold")
    w, h = text_wh(draw, text, fnt)
    draw.rounded_rectangle([x, y, x + w + 56, y + h + 32], radius=32, fill=bg)
    draw.text((x + 28, y + 14), text, font=fnt, fill=WHITE)
    return y + h + 32


def brand(draw, x: int = 40, y: int = 28, name: str = "Sangkan Clean"):
    ink(draw, (x, y), name, font(TYPE["brand"], "semibold"), TEAL)
    draw.rounded_rectangle([x, y + 40, x + 80, y + 48], radius=3, fill=CORAL)


def _base_photo(
    background: Path | Image.Image | None,
    size: tuple[int, int],
) -> Image.Image:
    if background is None:
        return branded_gradient(size)
    if isinstance(background, Image.Image):
        return cover_image(background, size)
    path = Path(background)
    if path.exists():
        return cover(path, size)
    return branded_gradient(size)


def compose(
    headline: str,
    subline: str = "",
    *,
    size: tuple[int, int] = FEED_SIZE,
    topic_id: str = "office_ondemand",
    brand_name: str = "Sangkan Clean",
    background: Path | Image.Image | None = None,
) -> Image.Image:
    w, h = size
    is_stories = h > w
    use_panel = topic_id == "price_pack" and not is_stories
    photo = _base_photo(background, size)

    if use_panel:
        img = photo
    else:
        img = wash_bottom(photo, 0.38 if is_stories else 0.42)

    draw = ImageDraw.Draw(img)
    brand(draw, name=brand_name)

    chip_text, chip_bg = CHIP_BY_TOPIC.get(topic_id, ("Sangkan Clean", CORAL))
    chip(draw, 40, 96, chip_text, chip_bg, DARK)

    if use_panel:
        panel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel)
        pd.rounded_rectangle(
            [24, 150, int(w * 0.62), h - 28],
            radius=28,
            fill=(255, 255, 255, 240),
        )
        img = Image.alpha_composite(img.convert("RGBA"), panel).convert("RGB")
        draw = ImageDraw.Draw(img)
        x, y = 48, 176
        # Match default Gen-Z type scale; keep text in left ~55% of frame
        head_f = font(TYPE["headline_feed"], "bold")
        for line in wrap_lines(draw, headline, head_f, int(w * 0.52))[
            : TYPE["headline_wrap_max"]
        ]:
            ink(draw, (x, y), line, head_f, INK, shadow=False)
            y += TYPE["headline_leading_feed"]
        if subline:
            y += 10
            sub_f = font(TYPE["subline_feed"], "medium")
            for line in wrap_lines(draw, subline, sub_f, int(w * 0.52))[
                : TYPE["subline_wrap_max"]
            ]:
                ink(draw, (x, y), line, sub_f, MUTED, shadow=False)
                y += TYPE["subline_leading"]
        cta(draw, x, min(y + 28, h - 130), "ทัก LINE @sangkanclean", TEAL)
    else:
        # Keep overlay in left ~55% so it sits in the clear left third of the photo
        max_w = int(w * (0.72 if is_stories else 0.55))
        y = int(h * (0.44 if is_stories else 0.40))
        head_f = font(
            TYPE["headline_stories"] if is_stories else TYPE["headline_feed"],
            "bold",
        )
        head_lead = (
            TYPE["headline_leading_stories"]
            if is_stories
            else TYPE["headline_leading_feed"]
        )
        for line in wrap_lines(draw, headline, head_f, max_w)[: TYPE["headline_wrap_max"]]:
            ink(draw, (40, y), line, head_f, WHITE)
            y += head_lead
        if subline:
            y += 10
            sub_f = font(
                TYPE["subline_stories"] if is_stories else TYPE["subline_feed"],
                "medium",
            )
            for line in wrap_lines(draw, subline, sub_f, max_w)[: TYPE["subline_wrap_max"]]:
                ink(draw, (40, y), line, sub_f, SOFT)
                y += TYPE["subline_leading"]
        cta(draw, 40, min(y + 28, h - 130), "ทัก LINE @sangkanclean")

    return ImageEnhance.Color(img).enhance(1.08)


def save_feed(
    headline: str,
    subline: str,
    path: Path,
    *,
    topic_id: str = "office_ondemand",
    background: Path | Image.Image | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    compose(
        headline,
        subline,
        size=FEED_SIZE,
        topic_id=topic_id,
        background=background,
    ).save(path, "PNG", optimize=True)
    return path


def save_stories(
    headline: str,
    subline: str,
    path: Path,
    *,
    topic_id: str = "office_ondemand",
    background: Path | Image.Image | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    compose(
        headline,
        subline,
        size=STORIES_SIZE,
        topic_id=topic_id,
        background=background,
    ).save(path, "PNG", optimize=True)
    return path
