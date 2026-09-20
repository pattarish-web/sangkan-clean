#!/usr/bin/env python3
"""Emergency local uploader. Production uploads from the webhook on confirm.

Dry-run by default. Prefer POST /api/leads/ads-conversions/upload on Render.
Do not import CSV if the API already uploaded the same order_id.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from google_ads.config import TARGET_CUSTOMER_ID, missing_credentials
from google_ads.upload_payload import ACTION_NAMES, ads_datetime, click_conversion_body


def _norm_id(customer_id: str) -> str:
    return str(customer_id).replace("-", "").strip()


def pending_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("conversions") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("upload_status") == "uploaded":
            continue
        if not row.get("gclid") or not row.get("conversion_name"):
            continue
        if row.get("conversion_name") not in ACTION_NAMES:
            continue
        out.append(row)
    return out


def load_leads_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _action_map(client: Any, customer_id: str) -> dict[str, str]:
    ga = client.get_service("GoogleAdsService")
    names = ", ".join(f"'{n}'" for n in ACTION_NAMES)
    query = f"""
      SELECT conversion_action.resource_name, conversion_action.name
      FROM conversion_action
      WHERE conversion_action.name IN ({names})
        AND conversion_action.status != 'REMOVED'
    """
    out: dict[str, str] = {}
    for row in ga.search(customer_id=_norm_id(customer_id), query=query):
        out[row.conversion_action.name] = row.conversion_action.resource_name
    return out


def upload_rows(client: Any, customer_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    actions = _action_map(client, customer_id)
    service = client.get_service("ConversionUploadService")
    request = client.get_type("UploadClickConversionsRequest")
    request.customer_id = _norm_id(customer_id)
    request.partial_failure = True
    used: list[dict[str, Any]] = []
    skipped_missing: list[str] = []
    for row in rows:
        resource = actions.get(row["conversion_name"])
        if not resource:
            skipped_missing.append(row["conversion_name"])
            continue
        body = click_conversion_body(row, resource)
        conversion = client.get_type("ClickConversion")
        conversion.gclid = body["gclid"]
        conversion.conversion_action = body["conversion_action"]
        conversion.conversion_date_time = body["conversion_date_time"] or ads_datetime(
            row.get("conversion_time") or ""
        )
        conversion.order_id = body["order_id"]
        conversion.currency_code = body["currency_code"]
        if "conversion_value" in body:
            conversion.conversion_value = body["conversion_value"]
        request.conversions.append(conversion)
        used.append(row)
    if not request.conversions:
        return {
            "uploaded": 0,
            "failed": 0,
            "missing_actions": skipped_missing,
            "results": [],
        }
    response = service.upload_click_conversions(request=request)
    results = []
    uploaded = 0
    failed = 0
    api_results = list(response.results)
    for i, row in enumerate(used):
        item = api_results[i] if i < len(api_results) else None
        ok = bool(item and (getattr(item, "gclid", "") or getattr(item, "conversion_action", "")))
        if ok:
            uploaded += 1
            results.append(
                {
                    "order_id": row.get("order_id"),
                    "conversion_name": row.get("conversion_name"),
                    "upload_status": "uploaded",
                }
            )
        else:
            failed += 1
            results.append(
                {
                    "order_id": row.get("order_id"),
                    "conversion_name": row.get("conversion_name"),
                    "upload_status": "failed",
                }
            )
    return {
        "uploaded": uploaded,
        "failed": failed,
        "missing_actions": skipped_missing,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Upload queued conversions to Google Ads.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--leads-file",
        default=str(_REPO / "ops/webhook/data/leads.json"),
        help="Local leads.json from the webhook store.",
    )
    parser.add_argument("--customer-id", default=TARGET_CUSTOMER_ID)
    args = parser.parse_args(argv)

    missing = missing_credentials()
    path = Path(args.leads_file)
    rows: list[dict[str, Any]] = []
    if path.exists():
        rows = pending_rows(load_leads_file(path))
        print(f"Pending conversions in {path}: {len(rows)}")
    else:
        print(f"No leads file at {path} (ok if webhook uses another store).")

    if missing:
        print("Missing credentials:", ", ".join(missing))
        print("Copy google_ads/ads_api.example.env to .env — never commit it.")
        if args.apply:
            print("Refusing --apply without credentials.")
            return 2
        return 1

    if not args.apply:
        print("Dry-run only. Names that will upload:", sorted({r["conversion_name"] for r in rows}) or "(none)")
        print("Re-run with --apply to call ConversionUploadService.")
        return 0

    from google_ads.client import get_client

    client = get_client(target_customer_id=args.customer_id)
    result = upload_rows(client, args.customer_id, rows)
    print(json.dumps({k: result[k] for k in ("uploaded", "failed", "missing_actions")}, ensure_ascii=False))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
