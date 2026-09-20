"""Build Google Ads click-conversion payloads. Never include PII."""

from __future__ import annotations

from typing import Any

ACTION_NAMES = ("phone_click", "line_click", "qualified_lead", "won_deal")


def ads_datetime(iso: str) -> str:
    if not iso:
        return ""
    s = str(iso).strip().replace("T", " ")
    if "." in s:
        head, rest = s.split(".", 1)
        tz = ""
        for sep in ("+", "-", "Z"):
            if sep in rest:
                tz = rest[rest.index(sep) :].replace("Z", "+00:00")
                break
        s = head + tz
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return s


def click_conversion_body(row: dict[str, Any], action_resource: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "gclid": str(row.get("gclid") or ""),
        "conversion_action": action_resource,
        "conversion_date_time": ads_datetime(str(row.get("conversion_time") or "")),
        "currency_code": str(row.get("conversion_currency") or "THB"),
        "order_id": str(row.get("order_id") or ""),
    }
    try:
        value = float(row.get("conversion_value") or 0)
    except (TypeError, ValueError):
        value = 0
    if value > 0:
        body["conversion_value"] = value
    return body


def payload_has_pii(payload: Any) -> bool:
    blob = str(payload)
    if '"name"' in blob or "'name'" in blob:
        return True
    if '"phone"' in blob or "'phone'" in blob:
        return True
    return False
