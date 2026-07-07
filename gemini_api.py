import json
import os
import time

import requests

# July 2026: gemini-pro / gemini-2.0-* are shut down. Use current models on v1beta.
DEFAULT_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
]


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


def call_gemini_json(
    api_key: str,
    prompt: str,
    *,
    max_retries: int = 3,
    base_delay: float = 15,
    timeout: int = 90,
) -> dict | None:
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    for model in get_models():
        url = build_generate_content_url(model, api_key)
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)

                if response.status_code == 404:
                    print(
                        f"  -> 404 Not Found – model '{model}' ไม่รองรับ "
                        f"({response.text[:160]})"
                    )
                    break

                if response.status_code == 429 or (
                    response.status_code == 400 and "RESOURCE_EXHAUSTED" in response.text
                ):
                    wait_time = base_delay * (1.5**attempt)
                    print(
                        f"  -> Rate limit hit for key {api_key[:10]}... "
                        f"Retry in {wait_time:.1f}s ({attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue

                if response.status_code != 200:
                    print(f"  -> API error {response.status_code}: {response.text[:300]}")
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (1.5**attempt)
                        print(f"  -> Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    break

                result_json = response.json()
                text_response = result_json["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_response)

            except requests.Timeout:
                print(f"  -> Request timeout ({attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(base_delay)
            except Exception as exc:
                if attempt == max_retries - 1:
                    print(f"  -> Gemini request failed: {exc}")
                    break
                wait_time = base_delay * (1.5**attempt)
                print(f"  -> Request failed ({exc}). Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)

    return None
