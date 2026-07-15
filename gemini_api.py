import json
import os
import threading
import time

import requests

from geo_log import log

# July 2026: gemini-pro / gemini-2.0-* are shut down. Use current models on v1beta.
DEFAULT_MODELS = [
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
]

_limiter_lock = threading.Lock()
_key_locks: dict[str, threading.Lock] = {}
_key_last_call: dict[str, float] = {}
_key_interval: dict[str, float] = {}
_key_429_strikes: dict[str, int] = {}
_exhausted_keys: set[str] = set()
# Free-tier RPD burns fast on retries — pause the key on first 429.
MAX_429_RETRIES = 1


def reset_429_strikes() -> None:
    """Clear per-key 429 state between retry passes."""
    with _limiter_lock:
        _key_429_strikes.clear()
        _exhausted_keys.clear()
        _key_interval.clear()


def is_key_exhausted(api_key: str) -> bool:
    return api_key in _exhausted_keys


def all_keys_exhausted(api_keys: list[str]) -> bool:
    return bool(api_keys) and all(k in _exhausted_keys for k in api_keys)


def active_keys_exhausted(api_keys: list[str], workers: int) -> bool:
    """True when every key assigned to a worker is paused."""
    if not api_keys:
        return True
    active = {api_keys[i % len(api_keys)] for i in range(min(workers, len(api_keys)))}
    return all(k in _exhausted_keys for k in active)


def clear_key_health(api_key: str) -> None:
    with _limiter_lock:
        _key_429_strikes.pop(api_key, None)
        _exhausted_keys.discard(api_key)
        _key_interval.pop(api_key, None)


def _base_interval() -> float:
    return float(os.environ.get("GEMINI_MIN_INTERVAL", "30"))


def _interval_for_key(api_key: str) -> float:
    return _key_interval.get(api_key, _base_interval())


def bump_key_cooldown(api_key: str, tag: str = "") -> float:
    """Slow down a key after 429 so we don't hammer the same quota."""
    with _limiter_lock:
        if api_key in _exhausted_keys:
            return _key_interval.get(api_key, _base_interval())
        current = _key_interval.get(api_key, _base_interval())
        new_interval = min(max(current * 1.5, current + 5), 45)
        _key_interval[api_key] = new_interval
        strikes = _key_429_strikes.get(api_key, 0) + 1
        _key_429_strikes[api_key] = strikes
        if strikes >= MAX_429_RETRIES:
            _exhausted_keys.add(api_key)
    label = tag or f"{api_key[:8]}…"
    shown = min(strikes, MAX_429_RETRIES)
    log(f"{label} cooldown → {new_interval:.0f}s/key (429 strike {shown}/{MAX_429_RETRIES})", level="WARN")
    return new_interval


def wait_for_key(api_key: str) -> None:
    """Per-key throttle so parallel workers don't burst the same project quota."""
    with _limiter_lock:
        if api_key not in _key_locks:
            _key_locks[api_key] = threading.Lock()
            _key_last_call[api_key] = 0.0
        key_lock = _key_locks[api_key]

    with key_lock:
        interval = _interval_for_key(api_key)
        now = time.monotonic()
        wait = interval - (now - _key_last_call[api_key])
        if wait > 0:
            time.sleep(wait)
        _key_last_call[api_key] = time.monotonic()


def get_models():
    override = os.environ.get("GEMINI_MODEL", "").strip()
    if override:
        return [override]
    return DEFAULT_MODELS


def build_generate_content_url(model: str, api_key: str) -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )


def _retry_wait(response: requests.Response | None, attempt: int, base_delay: float) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(max(float(retry_after), base_delay), 90)
            except ValueError:
                pass
    return min(base_delay * (2**attempt), 45)


def _429_strikes(api_key: str) -> int:
    return _key_429_strikes.get(api_key, 0)


def call_gemini_json(
    api_key: str,
    prompt: str,
    *,
    key_label: str = "",
    max_retries: int = 4,
    base_delay: float = 15,
    timeout: int = 90,
) -> dict | None:
    tag = key_label or f"{api_key[:8]}…"

    if is_key_exhausted(api_key):
        log(f"{tag} key paused (quota) — skip", level="WARN")
        return None

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    for model in get_models():
        url = build_generate_content_url(model, api_key)
        for attempt in range(max_retries):
            try:
                wait_for_key(api_key)
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)

                if response.status_code == 404:
                    log(
                        f"{tag} model '{model}' → 404 not found ({response.text[:120]})",
                        level="WARN",
                    )
                    break

                if response.status_code == 429 or (
                    response.status_code == 400 and "RESOURCE_EXHAUSTED" in response.text
                ):
                    # Don't retry/fall through models — each call burns daily quota.
                    bump_key_cooldown(api_key, tag)
                    log(f"{tag} RATE LIMIT (429) — pausing key (no retry)", level="WARN")
                    return None

                if response.status_code != 200:
                    log(f"{tag} API error {response.status_code}: {response.text[:200]}", level="WARN")
                    if attempt < max_retries - 1:
                        wait_time = _retry_wait(response, attempt, base_delay)
                        log(f"{tag} retry in {wait_time:.0f}s")
                        time.sleep(wait_time)
                        continue
                    break

                result_json = response.json()
                text_response = result_json["candidates"][0]["content"]["parts"][0]["text"]
                log(f"{tag} model '{model}' → success")
                clear_key_health(api_key)
                return json.loads(text_response)

            except requests.Timeout:
                log(f"{tag} timeout ({attempt + 1}/{max_retries})", level="WARN")
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
            except Exception as exc:
                if attempt == max_retries - 1:
                    log(f"{tag} failed after {max_retries} retries: {exc}", level="ERROR")
                    break
                wait_time = min(base_delay * (2**attempt), 90)
                log(f"{tag} error: {exc} → retry in {wait_time:.0f}s", level="WARN")
                time.sleep(wait_time)

    log(f"{tag} all models exhausted — giving up", level="ERROR")
    return None


def get_api_keys() -> list[str]:
    raw = os.environ.get("GEMINI_API_KEY", "")
    if not raw:
        return []
    if "," in raw:
        return [k.strip() for k in raw.split(",") if k.strip()]
    return [raw.strip()]


DEFAULT_IMAGE_MODELS = [
    os.environ.get("GEMINI_IMAGE_MODEL", "").strip() or "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
]


def call_gemini_image(
    api_key: str,
    prompt: str,
    *,
    key_label: str = "",
    timeout: int = 120,
) -> bytes | None:
    """Generate one image via Gemini image models; returns raw image bytes or None.

    On 429, tries the next image model on this key. Caller should rotate to the
    next API key when this returns None.
    """
    import base64

    tag = key_label or f"{api_key[:8]}…"
    if is_key_exhausted(api_key):
        log(f"{tag} key paused (quota) — skip image", level="WARN")
        return None

    models = [m for m in DEFAULT_IMAGE_MODELS if m]
    # Dedupe while preserving order
    seen = set()
    models = [m for m in models if not (m in seen or seen.add(m))]

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": "1:1"},
        },
    }
    headers = {"Content-Type": "application/json"}
    hit_429 = False

    for model in models:
        url = build_generate_content_url(model, api_key)
        try:
            wait_for_key(api_key)
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.Timeout:
            log(f"{tag} image timeout on {model}", level="WARN")
            continue
        except Exception as exc:
            log(f"{tag} image request error: {exc}", level="WARN")
            continue

        if response.status_code == 404:
            log(f"{tag} image model '{model}' → 404", level="WARN")
            continue

        if response.status_code == 429 or (
            response.status_code == 400 and "RESOURCE_EXHAUSTED" in response.text
        ):
            # Keep text key usable; try next image model, then caller rotates key.
            hit_429 = True
            retry_after = _retry_wait(response, 0, 8)
            log(
                f"{tag} image RATE LIMIT (429) on {model} — next model/key "
                f"(wait {retry_after:.0f}s)",
                level="WARN",
            )
            time.sleep(min(retry_after, 20))
            continue

        if response.status_code != 200:
            log(
                f"{tag} image API {response.status_code}: {response.text[:200]}",
                level="WARN",
            )
            continue

        try:
            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            log(f"{tag} image parse error: {exc}", level="WARN")
            continue

        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if not inline:
                continue
            b64 = inline.get("data")
            if not b64:
                continue
            log(f"{tag} image model '{model}' → success")
            clear_key_health(api_key)
            return base64.b64decode(b64)

        log(f"{tag} image model '{model}' returned no image parts", level="WARN")

    if hit_429:
        log(f"{tag} image 429 on all models — rotate to next API key", level="WARN")
    else:
        log(f"{tag} all image models failed", level="ERROR")
    return None


def call_gemini_json_rotate(
    api_keys: list[str],
    prompt: str,
    *,
    key_label_prefix: str = "gemini",
    **kwargs,
) -> dict | None:
    """Try each API key until JSON succeeds; skip keys paused after 429."""
    if not api_keys:
        return None
    for i, key in enumerate(api_keys):
        label = f"{key_label_prefix}-{i + 1}"
        if is_key_exhausted(key):
            log(f"{label} paused (quota) — try next key", level="WARN")
            continue
        data = call_gemini_json(key, prompt, key_label=label, **kwargs)
        if data and isinstance(data, dict):
            return data
        log(f"{label} JSON failed — try next key", level="WARN")
    return None


def call_gemini_image_rotate(
    api_keys: list[str],
    prompt: str,
    *,
    key_label_prefix: str = "gemini-img",
    **kwargs,
) -> bytes | None:
    """Try each API key until an image is returned."""
    if not api_keys:
        return None
    for i, key in enumerate(api_keys):
        label = f"{key_label_prefix}-{i + 1}"
        if is_key_exhausted(key):
            log(f"{label} paused (quota) — skip image key", level="WARN")
            continue
        if i > 0:
            # Stagger keys so we don't hammer shared project limits in the same second.
            time.sleep(3)
        log(f"{label} trying image ({i + 1}/{len(api_keys)})")
        raw = call_gemini_image(key, prompt, key_label=label, **kwargs)
        if raw:
            return raw
        log(f"{label} image failed — try next key", level="WARN")
    return None


def call_openai_json(
    prompt: str,
    *,
    model: str = "gpt-4o-mini",
    timeout: int = 90,
) -> dict | None:
    """Call OpenAI Chat Completions API with JSON response format and retry on 429."""
    import time
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        log("No OPENAI_API_KEY env var found", level="WARN")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }

    url = "https://api.openai.com/v1/chat/completions"
    max_retries = 3
    base_delay = 15
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if response.status_code == 429:
                wait_time = base_delay * (2 ** attempt)
                log(f"OpenAI API 429 Rate Limit. Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})", level="WARN")
                time.sleep(wait_time)
                continue
            if response.status_code != 200:
                log(f"OpenAI API error {response.status_code}: {response.text[:200]}", level="WARN")
                return None
            
            result_json = response.json()
            text_response = result_json["choices"][0]["message"]["content"]
            log(f"OpenAI model '{model}' → success")
            return json.loads(text_response)
        except Exception as exc:
            log(f"OpenAI error: {exc}", level="ERROR")
            if attempt < max_retries - 1:
                time.sleep(base_delay)
            else:
                return None
    return None

