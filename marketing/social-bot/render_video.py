"""Render short Ken Burns MP4 clips from still PNGs (ffmpeg)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def has_ffmpeg() -> bool:
    if shutil.which("ffmpeg"):
        return True
    try:
        import imageio_ffmpeg

        return bool(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        return False


def ken_burns(
    png_path: Path,
    mp4_path: Path,
    *,
    width: int,
    height: int,
    duration: float = 10.0,
    fps: int = 30,
) -> Path:
    """Slow zoom-in Ken Burns — readable text, no shake."""
    png_path = Path(png_path)
    mp4_path = Path(mp4_path)
    mp4_path.parent.mkdir(parents=True, exist_ok=True)

    frames = max(int(duration * fps), fps)
    # Mild zoom: end ~1.12x so type stays legible
    z_expr = f"min(1+0.12*on/{frames},1.12)"
    vf = (
        f"scale={width * 2}:{height * 2}:force_original_aspect_ratio=increase,"
        f"crop={width * 2}:{height * 2},"
        f"zoompan=z='{z_expr}':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={width}x{height}:fps={fps},"
        f"format=yuv420p"
    )

    cmd = [
        ffmpeg_bin(),
        "-y",
        "-loop",
        "1",
        "-i",
        str(png_path),
        "-vf",
        vf,
        "-t",
        str(duration),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an",
        str(mp4_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return mp4_path


def render_feed_clip(png_path: Path, mp4_path: Path, duration: float = 10.0) -> Path:
    return ken_burns(png_path, mp4_path, width=1080, height=1080, duration=duration)


def render_stories_clip(png_path: Path, mp4_path: Path, duration: float = 10.0) -> Path:
    return ken_burns(png_path, mp4_path, width=1080, height=1920, duration=duration)
