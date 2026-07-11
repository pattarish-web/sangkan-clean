"""LINE OA broadcast (Flex + optional image URL)."""

from __future__ import annotations

import os
from pathlib import Path

import requests

LINE_API = "https://api.line.me/v2/bot/message/broadcast"
SITE = "https://www.sangkanclean.com"
LINE_OA = "@sangkanclean"


def _token() -> str:
    return os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()


def _flex_bubble(headline: str, body: str, image_url: str | None) -> dict:
    contents: list[dict] = []
    if image_url:
        contents.append(
            {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "1:1",
                "aspectMode": "cover",
            }
        )
    contents.extend(
        [
            {
                "type": "text",
                "text": "Sangkan Clean",
                "weight": "bold",
                "size": "lg",
                "color": "#0f172a",
                "margin": "md",
            },
            {
                "type": "text",
                "text": headline[:40],
                "weight": "bold",
                "size": "md",
                "color": "#0d9488",
                "wrap": True,
                "margin": "sm",
            },
            {
                "type": "text",
                "text": body[:500],
                "size": "sm",
                "color": "#334155",
                "wrap": True,
                "margin": "md",
            },
        ]
    )
    bubble: dict = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#0d9488",
                    "action": {
                        "type": "uri",
                        "label": "ดูเว็บไซต์",
                        "uri": SITE,
                    },
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "uri",
                        "label": f"ทัก LINE {LINE_OA}",
                        "uri": "https://line.me/R/ti/p/@sangkanclean",
                    },
                },
            ],
        },
    }
    return bubble


def publish_line(
    *,
    text: str,
    image_path: Path | None,
    headline: str,
    dry_run: bool = False,
) -> dict:
    token = _token()
    base = os.environ.get("SOCIAL_ASSET_BASE_URL", "").rstrip("/")
    image_url = os.environ.get("SOCIAL_FEED_IMAGE_URL", "").strip() or None
    if not image_url and base and image_path:
        rel = str(image_path).replace("\\", "/")
        idx = rel.find("out/")
        if idx >= 0:
            image_url = f"{base}/{rel[idx:]}"

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "has_image_url": bool(image_url),
            "preview": text[:80],
        }
    if not token:
        return {
            "ok": False,
            "skipped": True,
            "reason": "missing LINE_CHANNEL_ACCESS_TOKEN",
        }

    messages = [
        {
            "type": "flex",
            "altText": headline[:100] or "Sangkan Clean",
            "contents": _flex_bubble(headline, text, image_url),
        }
    ]

    try:
        r = requests.post(
            LINE_API,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"messages": messages},
            timeout=60,
        )
        r.raise_for_status()
        return {"ok": True, "status_code": r.status_code}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
