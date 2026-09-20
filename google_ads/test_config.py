"""Credential requirements after the 2026-09-09 developer-token sunset."""

from __future__ import annotations

import unittest

from google_ads.config import CREDENTIAL_KEYS


class CredentialKeysTests(unittest.TestCase):
    def test_oauth_required_developer_token_optional(self) -> None:
        self.assertEqual(
            CREDENTIAL_KEYS,
            (
                "GOOGLE_ADS_CLIENT_ID",
                "GOOGLE_ADS_CLIENT_SECRET",
                "GOOGLE_ADS_REFRESH_TOKEN",
            ),
        )
        self.assertNotIn("GOOGLE_ADS_DEVELOPER_TOKEN", CREDENTIAL_KEYS)


if __name__ == "__main__":
    unittest.main()
