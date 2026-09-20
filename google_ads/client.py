"""Build a Google Ads API client from .env credentials."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from google.ads.googleads.client import GoogleAdsClient

from google_ads.config import (
    CLIENT_ID,
    CLIENT_SECRET,
    DEVELOPER_TOKEN,
    LOGIN_CUSTOMER_ID,
    REFRESH_TOKEN,
    require_credentials,
)


def _norm_id(customer_id: str) -> str:
    return str(customer_id).replace("-", "").strip()


def _base_config() -> dict:
    config = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "use_proto_plus": True,
    }
    if DEVELOPER_TOKEN:
        config["developer_token"] = DEVELOPER_TOKEN
    return config


def list_accessible_customer_ids(client: GoogleAdsClient) -> set[str]:
    service = client.get_service("CustomerService")
    response = service.list_accessible_customers()
    return {name.rsplit("/", 1)[-1] for name in response.resource_names}


def get_client(*, target_customer_id: str | None = None) -> GoogleAdsClient:
    """Create client with correct login-customer-id for direct vs MCC access."""
    require_credentials()
    config = _base_config()
    client = GoogleAdsClient.load_from_dict(config)

    if not target_customer_id:
        return client

    target = _norm_id(target_customer_id)
    accessible = list_accessible_customer_ids(client)

    # Direct access to the account: do not send MCC login header.
    if target in accessible:
        return client

    mcc = _norm_id(LOGIN_CUSTOMER_ID)
    if mcc in accessible:
        config["login_customer_id"] = int(mcc)
        return GoogleAdsClient.load_from_dict(config)

    raise SystemExit(
        f"Cannot access customer {target}. Accessible accounts: {sorted(accessible)}"
    )
