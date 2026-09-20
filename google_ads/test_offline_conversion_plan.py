"""Unit tests for Google Ads offline conversion planning (no API / no secrets)."""

from __future__ import annotations

import unittest

from google_ads.offline_conversion_plan import (
    DESIRED_NAMES,
    SK_BIGCLEAN_LANDING,
    VALUETRACK_SUFFIX,
    desired_actions,
    plan_setup,
    should_keep,
    should_pause_as_ads_goal,
    summarize_plan,
)


class DesiredActionsTests(unittest.TestCase):
    def test_exact_names_and_upload_clicks(self) -> None:
        specs = desired_actions()
        self.assertEqual([s["name"] for s in specs], list(DESIRED_NAMES))
        for spec in specs:
            self.assertEqual(spec["type"], "UPLOAD_CLICKS")
            self.assertEqual(spec["default_currency_code"], "THB")
            self.assertLessEqual(spec["click_through_lookback_window_days"], 30)

    def test_won_deal_uses_uploaded_thb_value(self) -> None:
        won = next(s for s in desired_actions() if s["name"] == "won_deal")
        self.assertFalse(won["always_use_default_value"])
        self.assertEqual(won["category"], "CONVERTED_LEAD")
        self.assertFalse(won["primary_for_goal"])
        phone = next(s for s in desired_actions() if s["name"] == "phone_click")
        line = next(s for s in desired_actions() if s["name"] == "line_click")
        self.assertTrue(phone["primary_for_goal"])
        self.assertTrue(line["primary_for_goal"])


class PauseMatchingTests(unittest.TestCase):
    def test_keep_offline_and_generate_lead(self) -> None:
        self.assertTrue(should_keep({"name": "phone_click"}))
        self.assertTrue(should_keep({"name": "Sangkan Clean (web) generate_lead"}))
        self.assertFalse(should_pause_as_ads_goal({"name": "phone_click", "status": "ENABLED"}))
        self.assertFalse(
            should_pause_as_ads_goal(
                {"name": "Sangkan Clean (web) generate_lead", "status": "ENABLED", "type": "GOOGLE_ANALYTICS_4_CUSTOM"}
            )
        )
        self.assertTrue(
            should_pause_as_ads_goal(
                {"name": "qualified_lead", "status": "ENABLED", "type": "UPLOAD_CLICKS", "primary_for_goal": True}
            )
        )

    def test_pause_ga4_click_phone_and_click_line(self) -> None:
        self.assertTrue(
            should_pause_as_ads_goal(
                {
                    "name": "Sangkan Clean (web) click_phone",
                    "status": "ENABLED",
                    "type": "GOOGLE_ANALYTICS_4_CUSTOM",
                }
            )
        )
        self.assertTrue(
            should_pause_as_ads_goal(
                {
                    "name": "Sangkan Clean (web) click_line",
                    "status": "ENABLED",
                    "origin": "GOOGLE_ANALYTICS",
                }
            )
        )

    def test_does_not_pause_phone_click_as_if_it_were_click_phone(self) -> None:
        self.assertFalse(
            should_pause_as_ads_goal({"name": "phone_click", "status": "ENABLED", "type": "UPLOAD_CLICKS"})
        )
        self.assertFalse(
            should_pause_as_ads_goal({"name": "line_click", "status": "ENABLED", "type": "UPLOAD_CLICKS"})
        )

    def test_pause_click_to_call_types(self) -> None:
        self.assertTrue(
            should_pause_as_ads_goal({"name": "Calls from ads", "status": "ENABLED", "type": "CLICK_TO_CALL"})
        )
        self.assertTrue(
            should_pause_as_ads_goal({"name": "Website calls", "status": "ENABLED", "type": "WEBSITE_CALL"})
        )

    def test_pause_webpage_phone_and_line_clicks(self) -> None:
        self.assertTrue(
            should_pause_as_ads_goal({"name": "คลิกโทร", "status": "ENABLED", "type": "WEBPAGE"})
        )
        self.assertTrue(
            should_pause_as_ads_goal({"name": "LINE click", "status": "ENABLED", "type": "WEBPAGE"})
        )

    def test_hidden_already_paused(self) -> None:
        self.assertFalse(
            should_pause_as_ads_goal(
                {"name": "Sangkan Clean (web) click_phone", "status": "HIDDEN"}
            )
        )


class PlanSetupTests(unittest.TestCase):
    def test_empty_account_creates_four_and_needs_auto_tag(self) -> None:
        plan = plan_setup([], auto_tagging_enabled=False)
        self.assertEqual([c["name"] for c in plan["creates"]], list(DESIRED_NAMES))
        self.assertEqual(plan["pauses"], [])
        self.assertTrue(plan["auto_tagging"]["needed"])
        self.assertFalse(plan["valuetrack"]["mutate_campaigns"])
        self.assertEqual(plan["valuetrack"]["keep_landing"], SK_BIGCLEAN_LANDING)
        self.assertIn("campaignid", VALUETRACK_SUFFIX)

    def test_skips_existing_and_pauses_ga4_clicks(self) -> None:
        existing = [
            {"id": "1", "name": "phone_click", "status": "ENABLED", "type": "UPLOAD_CLICKS", "primary_for_goal": True},
            {
                "id": "2",
                "name": "Sangkan Clean (web) click_phone",
                "status": "ENABLED",
                "type": "GOOGLE_ANALYTICS_4_CUSTOM",
                "origin": "GOOGLE_ANALYTICS",
                "primary_for_goal": True,
            },
            {
                "id": "3",
                "name": "Sangkan Clean (web) generate_lead",
                "status": "ENABLED",
                "type": "GOOGLE_ANALYTICS_4_CUSTOM",
                "primary_for_goal": True,
            },
        ]
        plan = plan_setup(existing, auto_tagging_enabled=True)
        self.assertEqual([c["name"] for c in plan["creates"]], ["line_click", "qualified_lead", "won_deal"])
        self.assertEqual([p["name"] for p in plan["pauses"]], ["Sangkan Clean (web) click_phone"])
        self.assertFalse(plan["pauses"][0]["set_status_hidden"])
        self.assertFalse(plan["auto_tagging"]["needed"])
        self.assertTrue(any("generate_lead" in a["name"] for a in existing))
        self.assertEqual(plan["promotes"], [])
        summary = "\n".join(summarize_plan(plan))
        self.assertIn("line_click", summary)

    def test_does_not_repause_secondary_actions(self) -> None:
        existing = [
            {
                "id": "9",
                "name": "Sangkan Clean (web) click_line",
                "status": "ENABLED",
                "type": "GOOGLE_ANALYTICS_4_CUSTOM",
                "primary_for_goal": False,
            }
        ]
        plan = plan_setup(existing, auto_tagging_enabled=True)
        self.assertEqual(plan["pauses"], [])
        self.assertEqual(plan["already_paused"][0]["name"], "Sangkan Clean (web) click_line")

    def test_promotes_confirmed_phone_and_demotes_qualified(self) -> None:
        existing = [
            {
                "id": "1",
                "name": "phone_click",
                "status": "ENABLED",
                "type": "UPLOAD_CLICKS",
                "primary_for_goal": False,
            },
            {
                "id": "2",
                "name": "qualified_lead",
                "status": "ENABLED",
                "type": "UPLOAD_CLICKS",
                "primary_for_goal": True,
            },
            {
                "id": "3",
                "name": "Sangkan Clean (web) generate_lead",
                "status": "ENABLED",
                "type": "GOOGLE_ANALYTICS_4_CUSTOM",
                "primary_for_goal": False,
            },
        ]
        plan = plan_setup(existing, auto_tagging_enabled=True)
        self.assertEqual([p["name"] for p in plan["pauses"]], ["qualified_lead"])
        self.assertFalse(plan["pauses"][0]["set_status_hidden"])
        names = [p["name"] for p in plan["promotes"]]
        self.assertIn("phone_click", names)
        self.assertIn("Sangkan Clean (web) generate_lead", names)


if __name__ == "__main__":
    unittest.main()
