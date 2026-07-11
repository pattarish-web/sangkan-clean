"""Publish short video to TikTok Content Posting API (draft until audit)."""

from __future__ import annotations

import os
from pathlib import Path

import requests

TIKTOK_API = "https://open.tiktokapis.com"


def _access_token() -> str:
    return os.environ.get("TIKTOK_ACCESS_TOKEN", "").strip()


def publish_tiktok(
    *,
    caption: str,
    video_path: Path | None,
    dry_run: bool = False,
) -> dict:
    """Upload as inbox/draft by default (safer before app audit approval).

    Set TIKTOK_PUBLISH_MODE=public to attempt DIRECT_POST after audit.
    """
    token = _access_token()
    mode = os.environ.get("TIKTOK_PUBLISH_MODE", "draft").strip().lower()
    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "mode": mode,
            "has_video": bool(video_path and video_path.exists()),
        }
    if not token:
        return {"ok": False, "skipped": True, "reason": "missing TIKTOK_ACCESS_TOKEN"}
    if not video_path or not video_path.exists():
        return {"ok": False, "reason": "missing stories.mp4"}

    size = video_path.stat().st_size
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    # Inbox draft (no public post) until Content Posting audit is approved.
    post_info = {
        "title": caption[:150],
        "privacy_level": "SELF_ONLY",
        "disable_duet": False,
        "disable_comment": False,
        "disable_stitch": False,
    }
    source_info = {
        "source": "FILE_UPLOAD",
        "video_size": size,
        "chunk_size": size,
        "total_chunk_count": 1,
    }

    try:
        if mode == "public":
            init_url = f"{TIKTOK_API}/v2/post/publish/video/init/"
            body = {"post_info": {**post_info, "privacy_level": "PUBLIC_TO_EVERYONE"}, "source_info": source_info}
        else:
            # Pull into creator inbox / draft
            init_url = f"{TIKTOK_API}/v2/post/publish/inbox/video/init/"
            body = {"source_info": source_info}

        init = requests.post(init_url, headers=headers, json=body, timeout=60)
        init.raise_for_status()
        init_data = init.json().get("data") or {}
        upload_url = init_data.get("upload_url")
        publish_id = init_data.get("publish_id")
        if not upload_url:
            return {"ok": False, "error": f"no upload_url: {init.json()}"}

        with video_path.open("rb") as fh:
            raw = fh.read()
        up = requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(size),
                "Content-Range": f"bytes 0-{size - 1}/{size}",
            },
            data=raw,
            timeout=180,
        )
        up.raise_for_status()
        return {"ok": True, "mode": mode, "publish_id": publish_id}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
