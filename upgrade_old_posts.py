import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from queue import Queue

from gemini_api import call_gemini_json, reset_429_strikes
from geo_log import banner, format_eta, key_label, log, milestone, progress

DEFAULT_SLEEP = 15
DEFAULT_LIMIT = 0
MAX_RETRY_PASSES = 3
QUOTA_COOLDOWN_SEC = 180  # 3 min between retry passes
CHECKPOINT_EVERY = 5


def get_api_keys():
    raw_key = os.environ.get("GEMINI_API_KEY", "")
    if not raw_key:
        return []
    if "," in raw_key:
        return [k.strip() for k in raw_key.split(",") if k.strip()]
    return [raw_key.strip()]


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


def _upgrade_one(posts, api_keys, api_key, idx):
    post = posts[idx]
    new_content = generate_geo_content(api_keys, api_key, post["title"], post["description"])
    if new_content:
        post["content"] = new_content
        post["dateModified"] = datetime.today().strftime("%Y-%m-%d")
        return True
    return False


def save_posts(posts, path="posts.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    log("checkpoint → posts.json saved")


def _run_sequential(posts, pending_indices, api_keys, sleep_sec, t0):
    upgraded_count = 0
    failed_indices = []
    total = len(pending_indices)

    for n, idx in enumerate(pending_indices, 1):
        post = posts[idx]
        key = api_keys[(n - 1) % len(api_keys)]
        log(f"[{n}/{total}] {post['title'][:55]}")

        if _upgrade_one(posts, api_keys, key, idx):
            upgraded_count += 1
            save_posts(posts)
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

    def maybe_checkpoint():
        with state_lock:
            if state["done"] % CHECKPOINT_EVERY == 0 or state["done"] >= total:
                save_posts(posts)
                log(progress(state["done"], total, state["ok"], state["fail"], time.time() - t0))
                if state["done"] % 25 == 0:
                    milestone(
                        f"GEO checkpoint: {state['done']}/{total} "
                        f"({state['ok']} ok, {state['fail']} fail)"
                    )

    def worker(worker_id):
        key = api_keys[worker_id % len(api_keys)]
        label = key_label(api_keys, key)
        stagger = worker_id * 4
        if stagger:
            log(f"Worker {worker_id + 1} stagger start +{stagger}s")
            time.sleep(stagger)
        log(f"Worker {worker_id + 1} started → {label}")
        local_ok = 0
        local_fail = []

        while True:
            try:
                idx = work_queue.get_nowait()
            except Exception:
                break

            ok = _upgrade_one(posts, api_keys, key, idx)
            with state_lock:
                state["done"] += 1
                if ok:
                    state["ok"] += 1
                    local_ok += 1
                else:
                    state["fail"] += 1
                    local_fail.append(idx)

            maybe_checkpoint()
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
    if sleep_sec > 0:
        os.environ.setdefault("GEMINI_MIN_INTERVAL", str(sleep_sec))

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    already_geo = sum(1 for p in posts if "สรุปประเด็นสำคัญ" in p.get("content", ""))
    pending_indices = [
        i for i, p in enumerate(posts)
        if "สรุปประเด็นสำคัญ" not in p.get("content", "")
    ]

    if limit > 0:
        pending_indices = pending_indices[:limit]

    banner("GEO UPGRADE START")
    log(f"API keys: {len(api_keys)} | workers: {workers} | interval: {sleep_sec}s/key")
    log(f"Models: {os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash → 3.1-flash-lite → 3.5-flash')}")
    log(f"Posts total: {len(posts)} | already GEO: {already_geo} | pending: {len(pending_indices)}")
    for i, k in enumerate(api_keys, 1):
        log(f"  Key#{i}: {k[:8]}…{k[-4:]}")

    if not pending_indices:
        log("Nothing to upgrade — all posts already have GEO content")
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
    remaining = sum(
        1 for p in posts if "สรุปประเด็นสำคัญ" not in p.get("content", "")
    )

    banner("GEO UPGRADE DONE")
    milestone(
        f"FINISHED — upgraded {upgraded_count} posts | "
        f"{len(posts) - remaining}/{len(posts)} total GEO | "
        f"failed {len(failed_indices)} | elapsed {format_eta(elapsed)}"
    )
    log(f"Elapsed: {format_eta(elapsed)} | upgraded this run: {upgraded_count} | still failed: {len(failed_indices)}")
    log(f"Site status: {len(posts) - remaining}/{len(posts)} posts now have GEO content")
    log(f"Remaining pending: {remaining}")

    if failed_indices:
        log("Failed posts:", level="WARN")
        for idx in failed_indices:
            log(f"  ✗ {posts[idx]['title'][:60]}", level="WARN")

    if upgraded_count > 0:
        log("Rebuilding site…")
        try:
            import build_site
            build_site.build_all()
            log("Site rebuilt successfully")
        except Exception as e:
            log(f"Rebuild error: {e}", level="ERROR")

    return upgraded_count


def main():
    parser = argparse.ArgumentParser(description="GEO upgrade old blog posts")
    parser.add_argument(
        "--limit", type=int, default=int(os.environ.get("GEO_BATCH_LIMIT", "0")),
        help="Max posts per run (default 0=unlimited)",
    )
    parser.add_argument(
        "--sleep", type=float, default=float(os.environ.get("GEO_SLEEP_SEC", "6")),
        help="Min seconds between requests per API key (default 6)",
    )
    parser.add_argument(
        "--workers", type=int, default=int(os.environ.get("GEO_WORKERS", "0")),
        help="Parallel workers (default: min(keys,3))",
    )
    args = parser.parse_args()
    upgrade_posts(limit=args.limit, sleep_sec=args.sleep, workers=args.workers)


if __name__ == "__main__":
    main()
