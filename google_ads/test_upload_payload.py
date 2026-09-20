"""Tests for Ads click-conversion payload builders (no API / no secrets)."""

from __future__ import annotations

import unittest

from google_ads.upload_offline_conversions import pending_rows
from google_ads.upload_payload import ads_datetime, click_conversion_body, payload_has_pii


class AdsDatetimeTests(unittest.TestCase):
    def test_iso_to_ads_space_format(self) -> None:
        self.assertEqual(
            ads_datetime("2026-09-19T18:30:32+00:00"),
            "2026-09-19 18:30:32+00:00",
        )
        self.assertEqual(
            ads_datetime("2026-09-19T18:30:32.000Z"),
            "2026-09-19 18:30:32+00:00",
        )


class PayloadTests(unittest.TestCase):
    def test_body_has_gclid_not_pii(self) -> None:
        body = click_conversion_body(
            {
                "gclid": "GCLID-1",
                "conversion_name": "phone_click",
                "conversion_time": "2026-09-19T18:30:32+00:00",
                "conversion_value": "",
                "conversion_currency": "THB",
                "order_id": "LD-1",
                "name": "SECRET",
                "phone": "0812345678",
            },
            "customers/6151208199/conversionActions/1",
        )
        blob = str(body)
        self.assertEqual(body["gclid"], "GCLID-1")
        self.assertNotIn("SECRET", blob)
        self.assertNotIn("0812345678", blob)
        self.assertFalse(payload_has_pii(body))

    def test_won_includes_value(self) -> None:
        body = click_conversion_body(
            {
                "gclid": "GCLID-2",
                "conversion_time": "2026-09-19T18:30:32+00:00",
                "conversion_value": 18500,
                "order_id": "LD-2",
            },
            "customers/1/conversionActions/2",
        )
        self.assertEqual(body["conversion_value"], 18500.0)


class PendingRowsTests(unittest.TestCase):
    def test_skips_uploaded_and_incomplete(self) -> None:
        rows = pending_rows(
            {
                "conversions": [
                    {
                        "gclid": "G1",
                        "conversion_name": "phone_click",
                        "upload_status": "pending",
                    },
                    {
                        "gclid": "G2",
                        "conversion_name": "line_click",
                        "upload_status": "uploaded",
                    },
                    {"gclid": "", "conversion_name": "won_deal"},
                ]
            }
        )
        self.assertEqual([r["gclid"] for r in rows], ["G1"])


if __name__ == "__main__":
    unittest.main()
