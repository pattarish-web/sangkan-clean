"""Structured logging for GEO upgrade — visible in GitHub Actions."""

import os
import threading
from datetime import datetime

_lock = threading.Lock()
_IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"


def log(msg: str, *, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    with _lock:
        print(f"[{ts}] [{level}] {msg}", flush=True)
        if _IN_CI and level in ("WARN", "ERROR"):
            print(f"::{level.lower()}::{msg}", flush=True)


def milestone(msg: str) -> None:
    """High-visibility line in GitHub Actions log."""
    log(msg)
    if _IN_CI:
        with _lock:
            print(f"::notice::{msg}", flush=True)


def banner(title: str) -> None:
    line = "=" * 60
    log(line)
    log(title)
    log(line)


def key_label(api_keys: list[str], key: str) -> str:
    try:
        idx = api_keys.index(key) + 1
    except ValueError:
        idx = "?"
    return f"Key#{idx}({key[:8]}…)"


def format_eta(seconds: float) -> str:
    if seconds <= 0 or seconds > 86400:
        return "—"
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def progress(done: int, total: int, ok: int, fail: int, elapsed: float) -> str:
    pct = (done / total * 100) if total else 100
    rate = done / elapsed if elapsed > 0 else 0
    eta = (total - done) / rate if rate > 0 else 0
    return (
        f"progress {done}/{total} ({pct:.0f}%) | "
        f"ok={ok} fail={fail} | "
        f"elapsed={format_eta(elapsed)} | ETA≈{format_eta(eta)}"
    )
