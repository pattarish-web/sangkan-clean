"""Publish to Facebook Page + Instagram via Meta Graph API."""

from __future__ import annotations

import os
import time
from pathlib import Path

import requests

GRAPH = "https://graph.facebook.com/v21.0"


def _token() -> str:
    return os.environ.get("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()


def _page_id() -> str:
    return os.environ.get("FACEBOOK_PAGE_ID", "").strip()


def _ig_id() -> str:
    return os.environ.get("INSTAGRAM_BUSINESS_ACCOUNT_ID", "").strip()


def publish_facebook(
    *,
    caption: str,
    image_path: Path | None,
    video_path: Path | None = None,
    dry_run: bool = False,
) -> dict:
    page_id = _page_id()
    token = _token()
    if dry_run:
        mode = "video" if video_path and video_path.exists() else "photo"
        return {
            "ok": True,
            "dry_run": True,
            "mode": mode,
            "page_id": page_id or None,
        }
    if not page_id or not token:
        return {"ok": False, "skipped": True, "reason": "missing FACEBOOK_PAGE_ID or token"}

    try:
        if video_path and video_path.exists():
            with video_path.open("rb") as fh:
                r = requests.post(
                    f"{GRAPH}/{page_id}/videos",
                    data={"description": caption, "access_token": token},
                    files={"source": fh},
                    timeout=180,
                )
            r.raise_for_status()
            data = r.json()
            return {"ok": True, "mode": "video", "id": data.get("id")}

        if not image_path or not image_path.exists():
            return {"ok": False, "reason": "missing feed image"}

        with image_path.open("rb") as fh:
            r = requests.post(
                f"{GRAPH}/{page_id}/photos",
                data={"caption": caption, "access_token": token},
                files={"source": fh},
                timeout=120,
            )
        r.raise_for_status()
        data = r.json()
        return {"ok": True, "mode": "photo", "id": data.get("id") or data.get("post_id")}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _ig_publish_container(ig_user_id: str, token: str, creation_id: str) -> dict:
    # Poll until finished
    for _ in range(30):
        st = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        st.raise_for_status()
        code = (st.json() or {}).get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            return {"ok": False, "error": f"IG container error: {st.json()}"}
        time.sleep(2)

    pub = requests.post(
        f"{GRAPH}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    pub.raise_for_status()
    return {"ok": True, "id": pub.json().get("id")}


def publish_instagram(
    *,
    caption: str,
    image_path: Path | None,
    video_path: Path | None = None,
    use_reels: bool = False,
    dry_run: bool = False,
) -> dict:
    """IG Content Publishing needs a publicly reachable media URL.

    Set SOCIAL_ASSET_BASE_URL to a CDN/raw GitHub URL prefix that serves
    marketing/social-bot/out/... files, OR set SOCIAL_FEED_IMAGE_URL /
    SOCIAL_REELS_VIDEO_URL for an explicit override.
    """
    ig_id = _ig_id()
    token = _token()
    if dry_run:
        mode = "reels" if use_reels and video_path else "image"
        return {"ok": True, "dry_run": True, "mode": mode, "ig_id": ig_id or None}
    if not ig_id or not token:
        return {
            "ok": False,
            "skipped": True,
            "reason": "missing INSTAGRAM_BUSINESS_ACCOUNT_ID or token",
        }

    base = os.environ.get("SOCIAL_ASSET_BASE_URL", "").rstrip("/")
    override_img = os.environ.get("SOCIAL_FEED_IMAGE_URL", "").strip()
    override_vid = os.environ.get("SOCIAL_REELS_VIDEO_URL", "").strip()

    try:
        if use_reels and video_path and video_path.exists():
            video_url = override_vid
            if not video_url and base:
                # Expect assets relative like out/YYYYMMDD/stories.mp4
                rel = str(video_path).replace("\\", "/")
                idx = rel.find("out/")
                if idx >= 0:
                    video_url = f"{base}/{rel[idx:]}"
            if not video_url:
                return {
                    "ok": False,
                    "skipped": True,
                    "reason": "IG Reels need public video URL (SOCIAL_ASSET_BASE_URL)",
                }
            create = requests.post(
                f"{GRAPH}/{ig_id}/media",
                data={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption,
                    "access_token": token,
                },
                timeout=60,
            )
            create.raise_for_status()
            creation_id = create.json().get("id")
            result = _ig_publish_container(ig_id, token, creation_id)
            result["mode"] = "reels"
            return result

        image_url = override_img
        if not image_url and base and image_path:
            rel = str(image_path).replace("\\", "/")
            idx = rel.find("out/")
            if idx >= 0:
                image_url = f"{base}/{rel[idx:]}"
        if not image_url:
            return {
                "ok": False,
                "skipped": True,
                "reason": "IG image needs public URL (SOCIAL_ASSET_BASE_URL)",
            }
        create = requests.post(
            f"{GRAPH}/{ig_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": token,
            },
            timeout=60,
        )
        create.raise_for_status()
        creation_id = create.json().get("id")
        result = _ig_publish_container(ig_id, token, creation_id)
        result["mode"] = "image"
        return result
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
