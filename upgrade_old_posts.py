import argparse
import json
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from queue import Queue

from build_blogs import build_single_blog
from gemini_api import (
    active_keys_exhausted,
    all_keys_exhausted,
    call_gemini_json,
    is_key_exhausted,
    reset_429_strikes,
)
from geo_log import banner, format_eta, key_label, log, milestone, progress, success

DEFAULT_SLEEP = 30
DEFAULT_LIMIT = 0
MAX_RETRY_PASSES = 2
QUOTA_COOLDOWN_SEC = 300  # 5 min when all keys paused (was 15 — too slow)
PROGRESS_EVERY = 5
# Commit+push every N successes in Actions (1 = every post, slow).
DEFAULT_COMMIT_EVERY = 5

_save_lock = threading.Lock()
_quota_wait_lock = threading.Lock()
_git_configured = False
_pending_git_paths: set[str] = set()
_successes_since_push = 0


def get_api_keys():
    raw_key = os.environ.get("GEMINI_API_KEY", "")
    if not raw_key:
        return []
    if "," in raw_key:
        return [k.strip() for k in raw_key.split(",") if k.strip()]
    return [raw_key.strip()]


def _log_worker_key_plan(api_keys: list[str], workers: int) -> None:
    """Show which API key each parallel worker uses (requires one key per worker)."""
    log(f"Worker/key plan ({workers} workers, {len(api_keys)} keys):")
    for i in range(workers):
        key = api_keys[i % len(api_keys)]
        log(f"  Worker {i + 1} → {key_label(api_keys, key)}")
    if len(api_keys) > workers:
        spare = [key_label(api_keys, k) for k in api_keys[workers:]]
        log(f"  Spare keys (failover on 429): {', '.join(spare)}")
    if len(api_keys) < workers:
        log(
            f"Only {len(api_keys)} key(s) for {workers} workers — some workers will share a key via rotation",
            level="WARN",
        )


def generate_geo_content(api_keys, api_key, title, description):
    label = key_label(api_keys, api_key)
    log(f"{label} → generating: {title[:60]}")

    prompt = f"""คุณเป็นผู้เชี่ยวชาญด้านการทำความสะอาดและนักเขียนบทความ SEO/GEO (Generative Engine Optimization)
ช่วยเขียนบทความบล็อกภาษาไทยแบบเจาะลึก

ชื่อบทความ: "{title}"
คำอธิบาย: "{description}"

ข้อกำหนด (สำคัญมากสำหรับการทำ GEO เพื่อให้ AI นำไปอ้างอิง):
เนื้อหาบทความ (content) ต้องเป็นโค้ด HTML semantic ล้วนๆ (ไม่ต้องมี <html> <body> tag)
- <h2>สรุปประเด็นสำคัญ (Key Takeaways)</h2> ตามด้วย <ul><li> 3-4 ข้อสั้นๆ
- <h2>เนื้อหาหลัก</h2> อธิบายเนื้อหาแบบเจาะลึก มีการใช้ <strong> เพื่อเน้นคำสำคัญ
- <h2>ข้อมูลสถิติที่น่าสนใจ</h2> สร้างข้อมูลเชิงประมาณหรือแนวโน้มทั่วไปในอุตสาหกรรม (ไม่ใช่ตัวเลขเฉพาะบริษัท) พร้อมข้อความว่า "ข้อมูลโดยประมาณจากแนวโน้มอุตสาหกรรม"
- <h2>คำถามที่พบบ่อย (FAQ)</h2> ถามตอบ 2-3 ข้อแบบสั้นๆ ตรงประเด็น

ตอบกลับเป็น JSON format เท่านั้น:
{{"content": "<h2>สรุปประเด็น...</h2>..."}}"""

    parsed_result = call_gemini_json(api_key, prompt, key_label=label, timeout=90)
    if not parsed_result:
        log(f"{label} ✗ no response", level="WARN")
        return None

    content = parsed_result.get("content", "")
    if content and "สรุปประเด็นสำคัญ" in content:
        log(f"{label} ✓ OK ({len(content)} chars)")
        return content

    log(f"{label} ✗ invalid content (missing GEO marker)", level="WARN")
    return None


def _commit_every() -> int:
    try:
        return max(1, int(os.environ.get("GEO_COMMIT_EVERY", str(DEFAULT_COMMIT_EVERY))))
    except ValueError:
        return DEFAULT_COMMIT_EVERY


def _ensure_git_identity() -> None:
    global _git_configured
    if _git_configured:
        return
    subprocess.run(["git", "config", "user.name", "Sangkan Clean Upgrade Bot"], check=True)
    subprocess.run(["git", "config", "user.email", "bot@sangkanclean.com"], check=True)
    _git_configured = True


def _flush_git_push(note: str = "") -> bool:
    """Commit staged GEO files and push once (batched). Call under _save_lock."""
    global _pending_git_paths, _successes_since_push
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return False
    if os.environ.get("GEO_INCREMENTAL_COMMIT", "1") != "1":
        return False
    if not _pending_git_paths:
        return False

    _ensure_git_identity()
    paths = sorted(_pending_git_paths)
    subprocess.run(["git", "add", *paths], check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        _pending_git_paths.clear()
        _successes_since_push = 0
        return False

    n = max(_successes_since_push, 1)
    msg = f"chore: GEO +{n} posts [skip ci]"
    if note:
        msg = f"chore: GEO +{n} {note[:40]} [skip ci]"
    commit = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True)
    if commit.returncode != 0:
        log(f"git commit skipped: {commit.stderr.strip()}", level="WARN")
        return False

    # Prefer fast push; rebase only if rejected (avoids reset --hard every post).
    push = subprocess.run(
        ["git", "push", "origin", "HEAD:main"],
        capture_output=True,
        text=True,
    )
    if push.returncode != 0:
        log("git push rejected — pull --rebase then retry", level="WARN")
        try:
            subprocess.run(["git", "reset", "--hard"], check=True, capture_output=True, text=True)
            subprocess.run(["git", "clean", "-fd"], check=True, capture_output=True, text=True)
        except Exception as exc:
            log(f"git clean/reset failed: {exc}", level="WARN")
        pull = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            capture_output=True,
            text=True,
        )
        if pull.returncode != 0:
            log(f"git pull failed: {pull.stderr.strip()}", level="WARN")
            # Never leave conflict markers inside posts.json.
            subprocess.run(["git", "rebase", "--abort"], capture_output=True, text=True)
            subprocess.run(["git", "merge", "--abort"], capture_output=True, text=True)
            try:
                subprocess.run(["git", "reset", "--hard", "HEAD"], check=True, capture_output=True)
            except Exception:
                pass
            return False
        push = subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            capture_output=True,
            text=True,
        )
        if push.returncode != 0:
            log(f"git push failed: {push.stderr.strip()}", level="WARN")
            return False

    _pending_git_paths.clear()
    _successes_since_push = 0
    log(f"git push OK ({msg})")
    return True


def checkpoint_post(posts, idx: int, *, force_push: bool = False) -> None:
    """Save posts.json + one blog HTML; batch-push to GitHub in Actions."""
    global _successes_since_push
    post = posts[idx]
    title = post.get("title", "")
    short = title[:55]

    with _save_lock:
        with open("posts.json", "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        slug = build_single_blog(posts, idx)
        _pending_git_paths.add(f"blog/{slug}.html")
        _pending_git_paths.add("posts.json")
        _successes_since_push += 1
        every = _commit_every()
        should_push = force_push or _successes_since_push >= every
        pushed = _flush_git_push(short) if should_push else False
        pending_batch = _successes_since_push

    gemini_total = sum(1 for p in posts if p.get("geo_source") == "gemini")
    total_posts = len(posts)
    pending = total_posts - gemini_total
    if pushed:
        deploy = "LIVE on main (batched)"
    elif should_push:
        deploy = "checkpoint (push pending/failed)"
    else:
        deploy = f"saved ({pending_batch}/{every} until push)"
    success(
        f"{short} | {deploy} | blog/{slug}.html | "
        f"{gemini_total}/{total_posts} gemini done ({pending} pending)"
    )


def flush_pending_git() -> None:
    """Push any leftover batched commits (call at end of run)."""
    with _save_lock:
        if _flush_git_push("flush"):
            log("Flushed remaining GEO commits to main")


def _upgrade_one(posts, api_keys, api_key, idx):
    if is_key_exhausted(api_key):
        return "quota"

    post = posts[idx]
    if post.get("geo_source") == "gemini":
        return "skip"

    new_content = generate_geo_content(api_keys, api_key, post["title"], post["description"])
    if new_content:
        post["content"] = new_content
        post["dateModified"] = datetime.today().strftime("%Y-%m-%d")
        post["geo_source"] = "gemini"
        checkpoint_post(posts, idx)
        return "ok"
    if is_key_exhausted(api_key):
        return "quota"
    return "fail"


def _pick_key(api_keys, worker_id):
    """Pick a healthy key for this worker; rotate if assigned key is paused."""
    preferred = api_keys[worker_id % len(api_keys)]
    if not is_key_exhausted(preferred):
        return preferred
    for k in api_keys:
        if not is_key_exhausted(k):
            return k
    return preferred


def _wait_for_quota(api_keys, workers):
    if not active_keys_exhausted(api_keys, workers):
        return
    with _quota_wait_lock:
        if not active_keys_exhausted(api_keys, workers):
            return
        active_count = min(workers, len(api_keys))
        banner("ALL ACTIVE KEYS PAUSED — waiting for quota")
        log(f"Cooling down {QUOTA_COOLDOWN_SEC}s before retrying…", level="WARN")
        milestone(
            f"All {active_count} active API keys hit quota — pausing {QUOTA_COOLDOWN_SEC // 60} min "
            f"(free-tier daily quota may need until tomorrow)"
        )
        time.sleep(QUOTA_COOLDOWN_SEC)
        reset_429_strikes()
        log("Quota cooldown done — resuming")


def _run_sequential(posts, pending_indices, api_keys, sleep_sec, t0):
    upgraded_count = 0
    failed_indices = []
    total = len(pending_indices)
    workers = 1  # sequential mode always uses one active key slot

    n = 0
    while n < len(pending_indices):
        _wait_for_quota(api_keys, workers)
        idx = pending_indices[n]
        post = posts[idx]
        key = _pick_key(api_keys, n % len(api_keys))
        log(f"[{n + 1}/{total}] {post['title'][:55]}")

        result = _upgrade_one(posts, api_keys, key, idx)
        if result == "quota":
            continue
        if result == "skip":
            n += 1
            continue

        n += 1
        if result == "ok":
            upgraded_count += 1
        else:
            failed_indices.append(idx)

        elapsed = time.time() - t0
        log(progress(n, total, upgraded_count, len(failed_indices), elapsed))

        if sleep_sec > 0 and n < total:
            time.sleep(sleep_sec)

    return upgraded_count, failed_indices


def _run_parallel(posts, pending_indices, api_keys, workers, t0):
    upgraded_count = 0
    failed_indices = []
    work_queue = Queue()
    for idx in pending_indices:
        work_queue.put(idx)

    total = len(pending_indices)
    state = {"done": 0, "ok": 0, "fail": 0}
    state_lock = threading.Lock()

    def maybe_log_progress():
        with state_lock:
            if state["done"] % PROGRESS_EVERY == 0 or state["done"] >= total:
                log(progress(state["done"], total, state["ok"], state["fail"], time.time() - t0))
                if state["done"] % 25 == 0:
                    milestone(
                        f"GEO progress: {state['done']}/{total} "
                        f"({state['ok']} ok, {state['fail']} fail)"
                    )

    def worker(worker_id):
        label = ""
        stagger = worker_id * 1
        if stagger:
            log(f"Worker {worker_id + 1} stagger start +{stagger}s")
            time.sleep(stagger)
        log(f"Worker {worker_id + 1} started")
        local_ok = 0
        local_fail = []

        while True:
            _wait_for_quota(api_keys, workers)
            try:
                idx = work_queue.get_nowait()
            except Exception:
                break

            key = _pick_key(api_keys, worker_id)
            label = key_label(api_keys, key)
            result = _upgrade_one(posts, api_keys, key, idx)
            if result == "quota":
                work_queue.put(idx)
                _wait_for_quota(api_keys, workers)
                continue
            if result == "skip":
                work_queue.task_done()
                continue

            with state_lock:
                state["done"] += 1
                if result == "ok":
                    state["ok"] += 1
                    local_ok += 1
                else:
                    state["fail"] += 1
                    local_fail.append(idx)

            maybe_log_progress()
            work_queue.task_done()

        log(f"Worker {worker_id + 1} ({label}) finished → ok={local_ok} fail={len(local_fail)}")
        return local_ok, local_fail

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, i) for i in range(workers)]
        for fut in as_completed(futures):
            ok, fails = fut.result()
            upgraded_count += ok
            failed_indices.extend(fails)

    return upgraded_count, failed_indices


def upgrade_posts(limit=DEFAULT_LIMIT, sleep_sec=DEFAULT_SLEEP, workers=0):
    api_keys = get_api_keys()
    if not api_keys:
        log("GEMINI_API_KEY not found — aborting", level="ERROR")
        return 0

    workers = workers or min(len(api_keys), 3)
    if len(api_keys) >= 3 and workers < 3:
        log("Tip: use workers=3 with 3 API keys in GEMINI_API_KEY (one key per worker)", level="WARN")
    if workers > 1 and len(api_keys) < workers:
        log(
            f"workers={workers} but only {len(api_keys)} key(s) — add keys to GEMINI_API_KEY "
            f"(comma-separated) so each worker uses a different key",
            level="WARN",
        )
    elif workers == 3 and len(api_keys) != 3:
        log(
            f"Expected 3 API keys for 3 workers, found {len(api_keys)} in GEMINI_API_KEY",
            level="WARN",
        )
    if sleep_sec > 0:
        os.environ.setdefault("GEMINI_MIN_INTERVAL", str(sleep_sec))

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    # Preserve earlier Gemini posts that have GEO content but no source flag yet.
    for p in posts:
        if "สรุปประเด็นสำคัญ" in p.get("content", "") and not p.get("geo_source"):
            p["geo_source"] = "gemini"

    already_gemini = sum(1 for p in posts if p.get("geo_source") == "gemini")
    already_offline = sum(1 for p in posts if p.get("geo_source") == "offline")
    # Drain path: rewrite offline (or unmarked non-gemini) posts to Gemini quality.
    pending_indices = [
        i for i, p in enumerate(posts)
        if p.get("geo_source") != "gemini"
    ]

    if limit > 0:
        pending_indices = pending_indices[:limit]

    banner("GEO UPGRADE START (Gemini drain)")
    log(f"API keys: {len(api_keys)} | workers: {workers} | interval: {sleep_sec}s/key")
    log(f"Save mode: per-post checkpoint + git every {_commit_every()} ok" + (
        " (Actions)" if os.environ.get("GITHUB_ACTIONS") == "true" else ""
    ))
    log(f"Models: {os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash → 3.1-flash-lite → 3.5-flash')}")
    log(
        f"Posts total: {len(posts)} | gemini: {already_gemini} | offline: {already_offline} | "
        f"pending Gemini rewrite: {len(pending_indices)}"
    )
    for i, k in enumerate(api_keys, 1):
        log(f"  Key#{i}: {k[:8]}…{k[-4:]}")
    if workers > 1:
        _log_worker_key_plan(api_keys, workers)

    if not pending_indices:
        log("Nothing to upgrade — all posts already marked geo_source=gemini")
        return 0

    upgraded_count = 0
    failed_indices = []
    t0 = time.time()

    for pass_num in range(1 + MAX_RETRY_PASSES):
        if pass_num > 0:
            if not failed_indices:
                break
            banner(f"RETRY PASS {pass_num}/{MAX_RETRY_PASSES} — {len(failed_indices)} posts")
            log(f"Waiting {QUOTA_COOLDOWN_SEC}s for API quota recovery…")
            time.sleep(QUOTA_COOLDOWN_SEC)
            reset_429_strikes()
            for idx in failed_indices:
                log(f"  retry: {posts[idx]['title'][:55]}")
            pending_indices = failed_indices
            failed_indices = []

        if workers <= 1:
            ok, fails = _run_sequential(posts, pending_indices, api_keys, sleep_sec, t0)
        else:
            ok, fails = _run_parallel(posts, pending_indices, api_keys, workers, t0)

        upgraded_count += ok
        failed_indices = fails

    elapsed = time.time() - t0
    remaining = sum(1 for p in posts if p.get("geo_source") != "gemini")
    gemini_total = sum(1 for p in posts if p.get("geo_source") == "gemini")

    banner("GEO UPGRADE DONE")
    success(
        f"RUN COMPLETE — upgraded {upgraded_count} posts | "
        f"{gemini_total}/{len(posts)} gemini | failed {len(failed_indices)} | "
        f"elapsed {format_eta(elapsed)}"
    )
    milestone(
        f"FINISHED — upgraded {upgraded_count} posts to Gemini | "
        f"{gemini_total}/{len(posts)} geo_source=gemini | "
        f"failed {len(failed_indices)} | elapsed {format_eta(elapsed)}"
    )
    log(f"Elapsed: {format_eta(elapsed)} | upgraded this run: {upgraded_count} | still failed: {len(failed_indices)}")
    log(f"Site status: {gemini_total}/{len(posts)} posts now have Gemini GEO content")
    log(f"Remaining pending Gemini rewrite: {remaining}")

    if failed_indices:
        log("Failed posts:", level="WARN")
        for idx in failed_indices:
            log(f"  ✗ {posts[idx]['title'][:60]}", level="WARN")

    if upgraded_count > 0:
        flush_pending_git()
        log("Rebuilding site…")
        try:
            # Guard: never rebuild on conflict-marker corruption.
            with open("posts.json", encoding="utf-8") as f:
                raw = f.read()
            if "<<<<<<<" in raw or ">>>>>>>" in raw:
                raise ValueError("posts.json has unresolved git conflict markers")
            json.loads(raw)
            import build_site
            build_site.build_all()
            log("Site rebuilt successfully")
        except Exception as e:
            log(f"Rebuild error: {e}", level="ERROR")
    else:
        flush_pending_git()

    return upgraded_count


def main():
    parser = argparse.ArgumentParser(description="GEO upgrade old blog posts")
    parser.add_argument(
        "--limit", type=int, default=int(os.environ.get("GEO_BATCH_LIMIT", "0")),
        help="Max posts per run (default 0=unlimited)",
    )
    parser.add_argument(
        "--sleep", type=float, default=float(os.environ.get("GEO_SLEEP_SEC", "30")),
        help="Min seconds between requests per API key (default 30)",
    )
    parser.add_argument(
        "--workers", type=int, default=int(os.environ.get("GEO_WORKERS", "0")),
        help="Parallel workers (default: min(keys,3))",
    )
    args = parser.parse_args()
    upgrade_posts(limit=args.limit, sleep_sec=args.sleep, workers=args.workers)


if __name__ == "__main__":
    main()
