#!/usr/bin/env python3
"""Configure Sangkan Clean Google Ads offline conversions.

Dry-run by default. Does not print tokens or client secrets.

  python google_ads/setup_offline_conversions.py
  python google_ads/setup_offline_conversions.py --apply

Requires repo-root .env keys listed in google_ads/ads_api.example.env.
Target account: AW-18299765093 / customer 615-120-8199 (MCC 791-572-9299).
Does not change SK-BigClean-Search landing URL.
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
from google_ads.offline_conversion_plan import (
    DESIRED_NAMES,
    SK_BIGCLEAN_LANDING,
    VALUETRACK_SUFFIX,
    desired_actions,
    plan_setup,
    summarize_plan,
)

CONVERSION_QUERY = """
    SELECT
      conversion_action.id,
      conversion_action.name,
      conversion_action.status,
      conversion_action.type,
      conversion_action.category,
      conversion_action.origin,
      conversion_action.primary_for_goal,
      conversion_action.resource_name
    FROM conversion_action
    WHERE conversion_action.status != 'REMOVED'
"""

CUSTOMER_QUERY = """
    SELECT
      customer.id,
      customer.descriptive_name,
      customer.auto_tagging_enabled
    FROM customer
    LIMIT 1
"""

CAMPAIGN_QUERY = """
    SELECT
      campaign.id,
      campaign.name,
      campaign.status,
      campaign.final_url_suffix
    FROM campaign
    WHERE campaign.status != 'REMOVED'
"""


def _enum_name(value: Any) -> str:
    if value is None:
        return ""
    name = getattr(value, "name", None)
    if name:
        return str(name)
    return str(value)


def _norm_id(customer_id: str) -> str:
    return str(customer_id).replace("-", "").strip()


def _print_missing_env(missing: list[str]) -> None:
    print("Google Ads was NOT configured — credentials are missing.")
    print(f"Create {_REPO / '.env'} (gitignored) with:")
    for key in missing:
        print(f"  {key}=")
    print("Optional:")
    print("  GOOGLE_ADS_TARGET_CUSTOMER_ID=6151208199")
    print("  GOOGLE_ADS_LOGIN_CUSTOMER_ID=7915729299")
    print("  GOOGLE_ADS_DEVELOPER_TOKEN=   # leftover; Ads ignores it after 2026-09-09")
    print("Template: google_ads/ads_api.example.env")
    print("OAuth (once): place google_ads/client_secret.json then python google_ads/auth.py")
    print("Never commit .env or client_secret.json.")


def _action_from_row(row: Any) -> dict[str, Any]:
    ca = row.conversion_action
    primary = None
    if hasattr(ca, "primary_for_goal"):
        primary = bool(ca.primary_for_goal)
    return {
        "id": str(ca.id),
        "name": ca.name,
        "status": _enum_name(ca.status),
        "type": _enum_name(ca.type_),
        "category": _enum_name(ca.category),
        "origin": _enum_name(ca.origin),
        "primary_for_goal": primary,
        "resource_name": ca.resource_name,
    }


def fetch_state(client: Any, customer_id: str) -> dict[str, Any]:
    ga = client.get_service("GoogleAdsService")
    cid = _norm_id(customer_id)
    actions = [_action_from_row(row) for row in ga.search(customer_id=cid, query=CONVERSION_QUERY)]
    auto_tagging = None
    descriptive_name = ""
    for row in ga.search(customer_id=cid, query=CUSTOMER_QUERY):
        auto_tagging = bool(row.customer.auto_tagging_enabled)
        descriptive_name = row.customer.descriptive_name or ""
        break
    campaigns = []
    for row in ga.search(customer_id=cid, query=CAMPAIGN_QUERY):
        campaigns.append(
            {
                "id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": _enum_name(row.campaign.status),
                "final_url_suffix": row.campaign.final_url_suffix or "",
            }
        )
    return {
        "actions": actions,
        "auto_tagging_enabled": auto_tagging,
        "descriptive_name": descriptive_name,
        "campaigns": campaigns,
    }


def _set_update_mask(client: Any, operation: Any, message: Any) -> None:
    try:
        from google.api_core import protobuf_helpers

        client.copy_from(
            operation.update_mask,
            protobuf_helpers.field_mask(None, message._pb),
        )
        return
    except Exception:
        pass
    paths: list[str] = []
    pb = getattr(message, "_pb", None)
    if pb is not None:
        for field, _value in pb.ListFields():
            paths.append(field.name)
    if not paths and hasattr(operation.update_mask, "paths"):
        # last resort — callers should still set fields on the message
        pass
    for path in paths:
        operation.update_mask.paths.append(path)


def _enable_auto_tagging(client: Any, customer_id: str) -> str:
    cid = _norm_id(customer_id)
    customer_service = client.get_service("CustomerService")
    operation = client.get_type("CustomerOperation")
    customer = operation.update
    customer.resource_name = customer_service.customer_path(cid)
    customer.auto_tagging_enabled = True
    _set_update_mask(client, operation, customer)
    customer_service.mutate_customer(customer_id=cid, operation=operation)
    return "enabled auto-tagging"


def _create_conversion(client: Any, customer_id: str, spec: dict[str, Any]) -> str:
    cid = _norm_id(customer_id)
    service = client.get_service("ConversionActionService")
    categories = [spec["category"], "LEAD", "DEFAULT"]
    last_error: Exception | None = None
    for category in categories:
        operation = client.get_type("ConversionActionOperation")
        conversion_action = operation.create
        conversion_action.name = spec["name"]
        conversion_action.type_ = client.enums.ConversionActionTypeEnum.UPLOAD_CLICKS
        conversion_action.category = getattr(
            client.enums.ConversionActionCategoryEnum, category
        )
        conversion_action.status = client.enums.ConversionActionStatusEnum.ENABLED
        conversion_action.view_through_lookback_window_days = spec[
            "view_through_lookback_window_days"
        ]
        conversion_action.click_through_lookback_window_days = spec[
            "click_through_lookback_window_days"
        ]
        conversion_action.counting_type = getattr(
            client.enums.ConversionActionCountingTypeEnum, spec["counting_type"]
        )
        value_settings = conversion_action.value_settings
        value_settings.default_value = spec["default_value"]
        value_settings.always_use_default_value = spec["always_use_default_value"]
        value_settings.default_currency_code = spec["default_currency_code"]
        if "primary_for_goal" in spec:
            conversion_action.primary_for_goal = bool(spec["primary_for_goal"])
        try:
            response = service.mutate_conversion_actions(
                customer_id=cid, operations=[operation]
            )
            resource = response.results[0].resource_name
            extra = "" if category == spec["category"] else f" (category fallback {category})"
            return f"created {spec['name']} {resource}{extra}"
        except Exception as exc:
            last_error = exc
            msg = str(exc)
            if "DUPLICATE_NAME" in msg:
                return f"skipped {spec['name']} (already exists)"
            if category != categories[-1] and any(
                token in msg
                for token in (
                    "INVALID_ENUM_VALUE",
                    "INVALID_CONVERSION_CATEGORY",
                    "category",
                )
            ):
                continue
            raise
    raise last_error or RuntimeError(f"failed to create {spec['name']}")


def _pause_conversion(client: Any, customer_id: str, action: dict[str, Any]) -> str:
    cid = _norm_id(customer_id)
    service = client.get_service("ConversionActionService")
    resource_name = action.get("resource_name") or service.conversion_action_path(
        cid, str(action["id"])
    )
    notes: list[str] = []

    primary_op = client.get_type("ConversionActionOperation")
    primary = primary_op.update
    primary.resource_name = resource_name
    primary.primary_for_goal = False
    _set_update_mask(client, primary_op, primary)
    try:
        service.mutate_conversion_actions(customer_id=cid, operations=[primary_op])
        notes.append("primary_for_goal=false")
    except Exception as exc:
        notes.append(f"primary_for_goal skipped ({type(exc).__name__})")

    if action.get("set_status_hidden"):
        hidden_op = client.get_type("ConversionActionOperation")
        hidden = hidden_op.update
        hidden.resource_name = resource_name
        hidden.status = client.enums.ConversionActionStatusEnum.HIDDEN
        _set_update_mask(client, hidden_op, hidden)
        try:
            service.mutate_conversion_actions(customer_id=cid, operations=[hidden_op])
            notes.append("status=HIDDEN")
        except Exception as exc:
            notes.append(f"HIDDEN skipped ({type(exc).__name__})")

    return f"paused {action['name']} ({', '.join(notes) or 'no-op'})"


def _set_primary_for_goal(
    client: Any, customer_id: str, action: dict[str, Any], primary: bool
) -> str:
    cid = _norm_id(customer_id)
    service = client.get_service("ConversionActionService")
    resource_name = action.get("resource_name") or service.conversion_action_path(
        cid, str(action["id"])
    )
    operation = client.get_type("ConversionActionOperation")
    ca = operation.update
    ca.resource_name = resource_name
    ca.primary_for_goal = primary
    _set_update_mask(client, operation, ca)
    service.mutate_conversion_actions(customer_id=cid, operations=[operation])
    flag = "primary" if primary else "secondary"
    return f"set {action['name']} {flag}"


def apply_plan(client: Any, customer_id: str, plan: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    if plan["auto_tagging"]["needed"]:
        changed.append(_enable_auto_tagging(client, customer_id))
    for spec in plan["creates"]:
        changed.append(_create_conversion(client, customer_id, spec))
    for action in plan["pauses"]:
        changed.append(_pause_conversion(client, customer_id, action))
    for action in plan.get("promotes") or []:
        try:
            changed.append(_set_primary_for_goal(client, customer_id, action, True))
        except Exception as exc:
            changed.append(f"promote {action['name']} skipped ({type(exc).__name__})")
    for item in plan["already_present"]:
        if item.get("status") == "HIDDEN" and item["name"] in DESIRED_NAMES:
            cid = _norm_id(customer_id)
            service = client.get_service("ConversionActionService")
            operation = client.get_type("ConversionActionOperation")
            ca = operation.update
            ca.resource_name = service.conversion_action_path(cid, str(item["id"]))
            ca.status = client.enums.ConversionActionStatusEnum.ENABLED
            _set_update_mask(client, operation, ca)
            service.mutate_conversion_actions(customer_id=cid, operations=[operation])
            changed.append(f"re-enabled {item['name']}")
        wanted = item.get("wanted_primary")
        current = item.get("primary_for_goal")
        if wanted is False and current is True:
            try:
                changed.append(_set_primary_for_goal(client, customer_id, item, False))
            except Exception as exc:
                changed.append(f"demote {item['name']} skipped ({type(exc).__name__})")
        if wanted is True and current is False:
            try:
                changed.append(_set_primary_for_goal(client, customer_id, item, True))
            except Exception as exc:
                changed.append(f"promote {item['name']} skipped ({type(exc).__name__})")
    return changed


def _print_campaign_reminder(campaigns: list[dict[str, Any]]) -> None:
    print()
    print("Campaigns (read-only — not mutated):")
    if not campaigns:
        print("  (none listed)")
        return
    for campaign in campaigns:
        flag = ""
        name = campaign["name"]
        if "BigClean" in name or "Big Clean" in name:
            flag = f"  landing must stay {SK_BIGCLEAN_LANDING}"
        suffix = campaign["final_url_suffix"]
        suffix_note = f" suffix={suffix}" if suffix else " (no final URL suffix)"
        print(f"  - {name} [{campaign['status']}]{suffix_note}{flag}")
    print(f"ValueTrack (optional, do not replace landing): {VALUETRACK_SUFFIX}")


def _connect(customer_id: str) -> Any:
    from google_ads.client import get_client

    return get_client(target_customer_id=customer_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create offline conversions and pause raw click Ads goals."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Mutate the Ads account. Default is dry-run.",
    )
    parser.add_argument(
        "--customer-id",
        default=TARGET_CUSTOMER_ID,
        help="Google Ads customer ID (default 6151208199).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the plan as JSON (no secrets).",
    )
    args = parser.parse_args(argv)

    missing = missing_credentials()
    if missing:
        _print_missing_env(missing)
        plan = plan_setup([], auto_tagging_enabled=None)
        print()
        print("Dry-run plan (no API access):")
        for line in summarize_plan(plan):
            print(f"  {line}")
        print("Desired actions:")
        for spec in desired_actions():
            value_note = (
                "uploaded THB value"
                if spec["name"] == "won_deal"
                else "default 0 THB"
            )
            print(f"  - {spec['name']}  {spec['type']}  {spec['category']}  {value_note}")
        if args.apply:
            print("Refusing --apply without credentials.")
            return 2
        print()
        print("Next: paste credentials into .env, then rerun.")
        print("  python google_ads/setup_offline_conversions.py          # dry-run")
        print("  python google_ads/setup_offline_conversions.py --apply  # mutate")
        return 1

    try:
        client = _connect(args.customer_id)
        state = fetch_state(client, args.customer_id)
    except SystemExit as exc:
        print(exc)
        return 2
    except Exception as exc:
        print(f"API call failed: {type(exc).__name__}: {exc}")
        return 2

    plan = plan_setup(
        state["actions"],
        auto_tagging_enabled=state["auto_tagging_enabled"],
    )
    if args.json:
        print(json.dumps({"plan": plan, "live_actions": state["actions"]}, ensure_ascii=False, indent=2))
    else:
        print(f"Connected to {state['descriptive_name'] or args.customer_id}")
        print(f"Current conversion actions: {len(state['actions'])}")
        for action in state["actions"]:
            goal = "primary" if action.get("primary_for_goal") else "secondary/unknown"
            print(
                f"  - {action['name']}  {action['status']}  {action['type']}  {goal}"
            )
        print()
        print("Plan:")
        for line in summarize_plan(plan):
            print(f"  {line}")
        _print_campaign_reminder(state["campaigns"])

    if not args.apply:
        print()
        print("Dry-run only. Nothing was changed.")
        print("Re-run with --apply to enable auto-tagging, create missing")
        print("UPLOAD_CLICKS actions, and mark raw phone/LINE clicks non-biddable.")
        return 0

    try:
        changed = apply_plan(client, args.customer_id, plan)
    except Exception as exc:
        print(f"Apply failed: {type(exc).__name__}: {exc}")
        return 2

    print()
    if changed:
        print("Applied:")
        for item in changed:
            print(f"  - {item}")
    else:
        print("Nothing to apply — account already matches the plan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
