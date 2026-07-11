# -*- coding: utf-8 -*-
"""Shared creative standard for Sangkan Clean image + copy generation.

All future Gemini image / overlay / caption generators should import from here
instead of duplicating briefs or type scales.
"""

from __future__ import annotations

# --- Background image brief (English — for image models only) ---

BACKGROUND_BRIEF = (
    "Commercial lifestyle photography for Instagram ads, 1080x1080 square. "
    "Gen-Z / young startup agency vibe — bright, airy, energetic, not corporate stiff. "
    "Color palette cues in set dressing only: teal (#0d9488), coral/pink accents, "
    "soft yellow accents, clean whites. "
    "Leave clear negative space on the LEFT third for Thai text overlay "
    "(no text, letters, logos, watermarks, or UI in the image). "
    "Photorealistic, shallow depth of field, natural daylight, "
    "modern Bangkok office / cowork aesthetic. "
    "Young East/Southeast Asian professionals, casual-smart attire. "
    "Indoor plants, clean desks, no cluttered UI mockups."
)

DEFAULT_SCENE = (
    "modern Bangkok coworking office, young professionals, bright airy lifestyle photo"
)


def build_background_prompt(
    scene: str = "",
    *,
    topic_mood: str = "",
    extra: str = "",
) -> str:
    """Fixed Gen-Z brief + short English scene (and optional mood/extra)."""
    parts = [BACKGROUND_BRIEF]
    if topic_mood:
        parts.append(f"Topic mood: {topic_mood}.")
    parts.append(f"Scene: {(scene or DEFAULT_SCENE).strip()}.")
    if extra:
        parts.append(extra.strip())
    return " ".join(parts)


# --- Thai copy tone (for text / caption prompts) ---

THAI_TONE_RULES = (
    "โทน: สบายๆ มั่นใจ แม่นยำ — คุยกับทีมวัยใหม่ / เอเจนซี่ / สตาร์ทอัพ\n"
    "ห้ามสำนวนราชการ ห้ามขายแข็ง ห้ามยาวเยิ่น\n"
    "emoji ได้ไม่เกิน 1 ตัว และห้ามใส่ hashtag ในเนื้อหาหลัก"
)

SUBLINE_MAX = 36


def clip_subline(text: str, max_len: int = SUBLINE_MAX) -> str:
    s = (text or "").strip()
    return s[:max_len] if s else s


# --- Overlay type scale (1080 feed / 1080×1920 stories) ---

TYPE = {
    "brand": 32,
    "chip": 28,
    "headline_feed": 72,
    "headline_stories": 80,
    "subline_feed": 32,
    "subline_stories": 34,
    "cta": 34,
    "headline_leading_feed": 84,
    "headline_leading_stories": 88,
    "subline_leading": 44,
    "headline_wrap_max": 3,
    "subline_wrap_max": 2,
}
