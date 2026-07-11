"""Compose feed (1:1) and stories (9:16) graphics — agency/tech bright teal."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parent
FONTS_DIR = ROOT.parent / "ads-office-ondemand" / "fonts"

TEAL = (13, 148, 136)
TEAL_BRIGHT = (20, 184, 166)
TEAL_DEEP = (15, 118, 110)
DARK = (15, 23, 42)
INK = (30, 41, 59)
OFFWHITE = (248, 250, 252)
MUTED = (100, 116, 139)
AMBER = (245, 158, 11)
WHITE = (255, 255, 255)

FEED_SIZE = (1080, 1080)
STORIES_SIZE = (1080, 1920)

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


def polish(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    return ImageEnhance.Contrast(img).enhance(1.05)


def _bg_split(size: tuple[int, int], diagonal: bool = True) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size, OFFWHITE)
    draw = ImageDraw.Draw(img)
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    if diagonal:
        od.polygon(
            [(int(w * 0.55), 0), (w, 0), (w, h), (int(w * 0.38), h)],
            fill=(*TEAL, 255),
        )
        od.polygon(
            [(int(w * 0.78), 0), (w, 0), (w, h), (int(w * 0.58), h)],
            fill=(*TEAL_BRIGHT, 100),
        )
        od.line(
            [(int(w * 0.55), 0), (int(w * 0.38), h)],
            fill=(255, 255, 255, 180),
            width=2,
        )
    else:
        od.rectangle([0, int(h * 0.62), w, h], fill=(*TEAL, 255))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def compose(
    headline: str,
    subline: str = "",
    *,
    size: tuple[int, int] = FEED_SIZE,
    brand: str = "Sangkan Clean",
) -> Image.Image:
    w, h = size
    is_stories = h > w
    img = _bg_split(size, diagonal=not is_stories)
    draw = ImageDraw.Draw(img)

    pad = 64 if not is_stories else 72
    y = pad + (40 if is_stories else 20)

    label_f = font(22 if not is_stories else 26, "semibold")
    draw.text((pad, y), "OFFICE  ·  AGENCY  ·  TECH", fill=TEAL_DEEP, font=label_f)
    y += 44 if not is_stories else 56

    brand_f = font(52 if not is_stories else 58, "bold")
    draw.text((pad, y), brand, fill=DARK, font=brand_f)
    y += 70 if not is_stories else 80

    max_w = int(w * (0.48 if not is_stories else 0.82))
    head_f = font(40 if not is_stories else 48, "semibold")
    for line in wrap_lines(draw, headline, head_f, max_w)[:4]:
        draw.text((pad, y), line, fill=INK, font=head_f)
        y += 52 if not is_stories else 60

    if subline:
        y += 12
        sub_f = font(26 if not is_stories else 30, "medium")
        for line in wrap_lines(draw, subline, sub_f, max_w)[:3]:
            draw.text((pad, y), line, fill=MUTED, font=sub_f)
            y += 36 if not is_stories else 42

    url_f = font(24, "regular")
    url = "www.sangkanclean.com"
    uy = h - (90 if not is_stories else 120)
    draw.text((pad, uy), url, fill=MUTED, font=url_f)
    tw, _ = text_wh(draw, url, url_f)
    draw.rectangle([pad, uy + 34, pad + tw, uy + 37], fill=AMBER)

    rail = Image.new("RGBA", size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rail)
    rd.rectangle([0, h - 5, w, h], fill=(*TEAL, 255))
    img = Image.alpha_composite(img.convert("RGBA"), rail).convert("RGB")
    return polish(img)


def save_feed(headline: str, subline: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    compose(headline, subline, size=FEED_SIZE).save(path, "PNG", optimize=True)
    return path


def save_stories(headline: str, subline: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    compose(headline, subline, size=STORIES_SIZE).save(path, "PNG", optimize=True)
    return path
