import json
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from cardapi.models import (
    CCRewardRate,
    CardRewardProgram,
    CreditCard,
    Issuer,
    Perk,
    RewardCategory,
    RewardProgram,
    RewardProgramUnlock,
    RewardTransferRoute,
    SignupBonus,
    StatementCredit,
)
from cardapi.services.cardapi import (
    CardAPIClient,
    CardAPIConfigurationError,
    CardAPIDataError,
    import_cards_payload,
    import_curated_payload,
    import_perks_payload,
    import_statement_credits_payload,
)
from cardapi.services.coverage import build_coverage_report
from cardapi.services.comparison import compare_cards
from cardapi.services.portfolio import (
    BonusEligibility,
    SignupBonusUse,
    SpendingBucket,
    StatementCreditUse,
    analyze_candidate_cards,
    evaluate_portfolio,
)
from cardapi.services.reward_programs import import_reward_program_payload
from cardapi.services.goals import RewardGoal, match_reward_goals
from cardapi.services.transfer_partners import import_transfer_partner_payload
from cardapi.services.rewards import match_reward_rate


CARD_PAYLOAD = {
    "data": [
        {
            "issuer_id": "875b443c-1d31-48fd-a475-a9ca487e9749",
            "slug": "american-express-gold-card",
            "name": "American Express Gold Card",
            "network": "AMEX",
            "card_type": "personal",
            "annual_fee": 325,
            "annual_fee_waived_first_year": False,
            "signup_bonus": "Earn 60,000 Membership Rewards points",
            "signup_bonus_value": 60000,
            "signup_min_spend": 6000,
            "signup_min_spend_months": 6,
            "reward_currency": "MR",
            "reward_currency_name": "Membership Rewards",
            "application_rules": None,
            "is_discontinued": False,
            "updated_at": "2026-08-01T12:00:00+00:00",
            "issuers": {
                "name": "American Express",
                "slug": "amex-us",
                "country": "US",
                "website": "https://www.americanexpress.com",
                "logo_url": None,
            },
            "reward_rates": [
                {
                    "id": "7de6e7ac-d13a-4312-95c3-215d16aebfa3",
                    "card_id": "c2495eb2-eb53-4c4d-9bfb-6843f641f4ee",
                    "category_slug": "dining",
                    "rate_multiplier": 4,
                    "rate_type": "points_per_dollar",
                    "cap_amount": 50000,
                    "cap_period": "annual",
                    "fallback_rate": 1,
                    "is_base_rate": False,
                    "is_rotating": False,
                    "rotating_quarter": None,
                    "rotating_year": None,
                    "notes": "At restaurants worldwide.",
                    "created_at": "2026-07-18T18:08:42.116942+00:00",
                }
            ],
        }
    ]
}


class CardAPIMaintenanceCommandTests(TestCase):
    @staticmethod
    def _page(*slugs):
        records = []
        for slug in slugs:
            record = deepcopy(CARD_PAYLOAD["data"][0])
            record.update(
                {
                    "slug": slug,
                    "name": slug.replace("-", " ").title(),
                    "signup_bonus": None,
                    "signup_bonus_value": None,
                    "signup_min_spend": None,
                    "signup_min_spend_months": None,
                    "reward_rates": [],
                }
            )
            records.append(record)
        return {"data": records}

    @patch("cardapi.management.commands.run_cardapi_maintenance.CardAPIClient")
    def test_maintenance_paginates_imports_and_reports_coverage(self, client_class):
        client = client_class.return_value
        client.get_cards.side_effect = [
            self._page("maintenance-card-one", "maintenance-card-two"),
            self._page("maintenance-card-three"),
        ]
        output = StringIO()

        call_command(
            "run_cardapi_maintenance",
            country="US",
            page_size=2,
            max_pages=10,
            unavailable=["perks", "statement_credits"],
            stdout=output,
        )

        result = json.loads(output.getvalue())
        self.assertEqual(CreditCard.objects.count(), 3)
        self.assertEqual(result["sync"]["pages_fetched"], 2)
        self.assertEqual(result["sync"]["cards_received"], 3)
        self.assertEqual(result["coverage"]["summary"]["cards"], 3)
        self.assertEqual(
            result["coverage"]["summary"]["unavailable_features"],
            ["perks", "statement_credits"],
        )
        self.assertEqual(len(result["coverage"]["cards"]), 3)
        self.assertEqual(
            [call.kwargs["offset"] for call in client.get_cards.call_args_list],
            [0, 2],
        )
        self.assertTrue(
            all(
                call.kwargs == {"limit": 2, "offset": offset, "country": "US"}
                for call, offset in zip(client.get_cards.call_args_list, (0, 2))
            )
        )

    @patch("cardapi.management.commands.run_cardapi_maintenance.CardAPIClient")
    def test_maintenance_stops_repeated_pagination(self, client_class):
        repeated = self._page("maintenance-repeated-card")
        client_class.return_value.get_cards.side_effect = [repeated, repeated]

        with self.assertRaisesMessage(CommandError, "repeated"):
            call_command(
                "run_cardapi_maintenance",
                page_size=1,
                max_pages=10,
            )

    @patch("cardapi.management.commands.run_cardapi_maintenance.CardAPIClient")
    def test_maintenance_enforces_pagination_safety_limit(self, client_class):
        client_class.return_value.get_cards.return_value = self._page(
            "maintenance-full-page"
        )

        with self.assertRaisesMessage(CommandError, "reached --max-pages"):
            call_command(
                "run_cardapi_maintenance",
                page_size=1,
                max_pages=1,
            )

    def test_maintenance_validates_limits_before_requesting_cardapi(self):
        invalid_options = (
            {"page_size": 0},
            {"page_size": 101},
            {"max_pages": 0},
            {"stale_after_days": -1},
        )
        for options in invalid_options:
            with self.assertRaises(CommandError):
                call_command("run_cardapi_maintenance", **options)


class CatalogSnapshotRestoreTests(TestCase):
    def test_committed_snapshot_restores_a_usable_catalog(self):
        with self.assertRaisesMessage(CommandError, "--confirm-replace"):
            call_command("restore_cardapi_snapshot")

        call_command(
            "restore_cardapi_snapshot",
            "cardapi/data/catalog_snapshot_2026-09-02.json",
            confirm_replace=True,
            stdout=StringIO(),
        )

        self.assertGreater(CreditCard.objects.count(), 0)
        self.assertGreater(CCRewardRate.objects.count(), 0)
        self.assertGreater(SignupBonus.objects.count(), 0)
        self.assertGreater(StatementCredit.objects.count(), 0)
        self.assertGreater(Perk.objects.count(), 0)
        self.assertGreater(RewardProgram.objects.count(), 0)
        self.assertGreater(CardRewardProgram.objects.count(), 0)
        self.assertGreater(RewardProgramUnlock.objects.count(), 0)
        self.assertGreater(RewardTransferRoute.objects.count(), 0)

        gold = CreditCard.objects.get(local_slug="american-express-gold-card")
        self.assertTrue(gold.reward_rates.filter(is_active=True).exists())
        self.assertTrue(gold.reward_program_memberships.filter(is_active=True).exists())
        self.assertTrue(
            RewardTransferRoute.objects.filter(
                source_program__code="amex-membership-rewards",
                destination_program__code="aeroplan",
                is_active=True,
            ).exists()
        )
        report = build_coverage_report(country="US")
        self.assertEqual(report["summary"]["cards"], CreditCard.objects.count())
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_failed_restore_rolls_back_existing_catalog(self):
        issuer = Issuer.objects.create(
            slug="restore-rollback-bank",
            name="Restore Rollback Bank",
            country="US",
        )
        card = CreditCard.objects.create(
            local_slug="restore-rollback-card",
            issuer=issuer,
            name="Restore Rollback Card",
        )

        with self.assertRaises(CommandError):
            call_command(
                "restore_cardapi_snapshot",
                "cardapi/data/not-a-snapshot.json",
                confirm_replace=True,
                stdout=StringIO(),
            )

        self.assertTrue(CreditCard.objects.filter(pk=card.pk).exists())
        self.assertTrue(Issuer.objects.filter(pk=issuer.pk).exists())


class CardImportTests(TestCase):
    @patch.dict("os.environ", {"CARDAPI_KEY": "configured-test-key"}, clear=True)
    def test_client_reads_cardapi_key_environment_variable(self):
        self.assertEqual(CardAPIClient().api_key, "configured-test-key")

    @patch.dict("os.environ", {}, clear=True)
    def test_client_requires_cardapi_key_environment_variable(self):
        with self.assertRaises(CardAPIConfigurationError):
            CardAPIClient()

    def test_import_is_idempotent_and_does_not_infer_card_id(self):
        first = import_cards_payload(deepcopy(CARD_PAYLOAD))
        second = import_cards_payload(deepcopy(CARD_PAYLOAD))

        self.assertEqual(first.cards_created, 1)
        self.assertEqual(second.cards_created, 0)
        self.assertEqual(Issuer.objects.count(), 1)
        self.assertEqual(CreditCard.objects.count(), 1)
        self.assertEqual(CCRewardRate.objects.count(), 1)
        self.assertEqual(SignupBonus.objects.count(), 1)

        card = CreditCard.objects.get()
        self.assertIsNone(card.cardapi_id)
        self.assertEqual(card.issuer.slug, "amex-us")
        self.assertEqual(card.reward_currency, "MR")
        self.assertEqual(card.signup_bonuses.get().bonus_unit, RewardProgram.Unit.POINTS)

    def test_null_api_value_does_not_erase_existing_value(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        card.application_rules = "Curated eligibility rule"
        card.save(update_fields=["application_rules"])

        payload = deepcopy(CARD_PAYLOAD)
        payload["data"][0]["application_rules"] = None
        import_cards_payload(payload)

        card.refresh_from_db()
        self.assertEqual(card.application_rules, "Curated eligibility rule")

    def test_non_null_api_value_updates_existing_value(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        payload = deepcopy(CARD_PAYLOAD)
        payload["data"][0]["annual_fee"] = 350

        import_cards_payload(payload)

        card = CreditCard.objects.get()
        self.assertEqual(card.annual_fee, Decimal("350.00"))

    def test_new_bonus_deactivates_previous_bonus(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        payload = deepcopy(CARD_PAYLOAD)
        payload["data"][0]["signup_bonus"] = "Earn 75,000 points"
        payload["data"][0]["signup_bonus_value"] = 75000

        import_cards_payload(payload)

        self.assertEqual(SignupBonus.objects.count(), 2)
        self.assertEqual(SignupBonus.objects.filter(is_active=True).count(), 1)
        self.assertEqual(
            SignupBonus.objects.get(is_active=True).bonus_amount,
            Decimal("75000.0000"),
        )

    def test_returning_bonus_reactivates_existing_record(self):
        original = deepcopy(CARD_PAYLOAD)
        import_cards_payload(original)

        changed = deepcopy(CARD_PAYLOAD)
        changed["data"][0]["signup_bonus"] = "Earn 75,000 points"
        changed["data"][0]["signup_bonus_value"] = 75000
        import_cards_payload(changed)
        import_cards_payload(original)

        self.assertEqual(SignupBonus.objects.count(), 2)
        self.assertEqual(
            SignupBonus.objects.get(is_active=True).bonus_amount,
            Decimal("60000.0000"),
        )

    def test_incomplete_response_does_not_deactivate_reward_rate(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        payload = deepcopy(CARD_PAYLOAD)
        payload["data"][0]["reward_rates"] = []

        import_cards_payload(payload)

        self.assertTrue(CCRewardRate.objects.get().is_active)

    def test_authoritative_response_deactivates_missing_reward_rate(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        payload = deepcopy(CARD_PAYLOAD)
        payload["data"][0]["reward_rates"] = []

        import_cards_payload(payload, authoritative_child_data=True)

        self.assertFalse(CCRewardRate.objects.get().is_active)

    def test_incomplete_reward_rate_rolls_back_the_card(self):
        payload = deepcopy(CARD_PAYLOAD)
        del payload["data"][0]["reward_rates"][0]["id"]

        with self.assertRaises(CardAPIDataError):
            import_cards_payload(payload)

        self.assertEqual(CreditCard.objects.count(), 0)
        self.assertEqual(Issuer.objects.count(), 0)

    def test_curated_official_data_overrides_cardapi_value(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        curated = {
            "data": [
                {
                    "cardapi_slug": "american-express-gold-card",
                    "source_url": "https://www.americanexpress.com/example",
                    "verified_at": "2026-09-02",
                    "fields": {
                        "foreign_transaction_fee": 0,
                        "annual_fee": 999,
                    },
                }
            ]
        }

        import_curated_payload(curated)

        card = CreditCard.objects.get()
        self.assertEqual(card.foreign_transaction_fee, Decimal("0.0000"))
        self.assertEqual(card.annual_fee, Decimal("999.00"))
        self.assertEqual(
            card.product_url, "https://www.americanexpress.com/example"
        )
        self.assertIn("foreign_transaction_fee", card.curated_sources)
        self.assertEqual(
            card.curated_sources["annual_fee"]["previous_value"], "325.00"
        )

    def test_undated_cardapi_value_does_not_replace_curated_value(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        import_curated_payload(
            {
                "data": [
                    {
                        "cardapi_slug": "american-express-gold-card",
                        "source_url": "https://www.americanexpress.com/example",
                        "verified_at": "2026-09-02",
                        "fields": {"foreign_transaction_fee": 3},
                    }
                ]
            }
        )
        api_payload = deepcopy(CARD_PAYLOAD)
        api_payload["data"][0]["foreign_transaction_fee"] = 0
        del api_payload["data"][0]["updated_at"]

        import_cards_payload(api_payload)

        card = CreditCard.objects.get()
        self.assertEqual(card.foreign_transaction_fee, Decimal("3.0000"))
        self.assertIn("foreign_transaction_fee", card.curated_sources)

    def test_newer_dated_cardapi_value_replaces_curated_value(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        import_curated_payload(
            {
                "data": [
                    {
                        "cardapi_slug": "american-express-gold-card",
                        "source_url": "https://www.americanexpress.com/example",
                        "verified_at": "2026-09-02",
                        "fields": {"foreign_transaction_fee": 3},
                    }
                ]
            }
        )
        api_payload = deepcopy(CARD_PAYLOAD)
        api_payload["data"][0]["foreign_transaction_fee"] = 0
        api_payload["data"][0]["updated_at"] = "2026-10-01T00:00:00+00:00"

        import_cards_payload(api_payload)

        card = CreditCard.objects.get()
        self.assertEqual(card.foreign_transaction_fee, Decimal("0.0000"))
        self.assertNotIn("foreign_transaction_fee", card.curated_sources)

    def test_curated_data_requires_provenance(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))

        with self.assertRaises(CardAPIDataError):
            import_curated_payload(
                {
                    "data": [
                        {
                            "cardapi_slug": "american-express-gold-card",
                            "fields": {"foreign_transaction_fee": 0},
                        }
                    ]
                }
            )

    def test_curated_import_can_create_official_only_card(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))

        stats = import_curated_payload(
            {
                "data": [
                    {
                        "local_slug": "capital-one-savor-good-credit",
                        "name": "Savor Rewards for Good Credit",
                        "issuer_slug": "amex-us",
                        "source_url": "https://www.capitalone.com/example",
                        "verified_at": "2026-09-02",
                        "fields": {
                            "annual_fee": 0,
                            "product_family": "savor",
                            "recommended_credit_profile": "good",
                        },
                        "signup_bonuses": [],
                    }
                ]
            }
        )

        card = CreditCard.objects.get(
            local_slug="capital-one-savor-good-credit"
        )
        self.assertEqual(stats["cards_created"], 1)
        self.assertIsNone(card.cardapi_slug)
        self.assertEqual(card.product_family, "savor")
        self.assertEqual(card.recommended_credit_profile, "good")
        self.assertFalse(card.signup_bonuses.filter(is_active=True).exists())

    def test_statement_credit_payload_is_card_owned_and_idempotent(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        payload = {
            "data": [
                {
                    "id": "756906a3-e231-4bdc-9d43-2b8d108dc460",
                    "credit_name": "Dining Credit",
                    "credit_amount": 120,
                    "credit_period": "annual",
                    "eligible_merchants": "Selected dining partners",
                    "enrollment_required": False,
                    "notes": "$10 per month",
                }
            ]
        }

        import_statement_credits_payload("american-express-gold-card", payload)
        import_statement_credits_payload("american-express-gold-card", payload)

        self.assertEqual(StatementCredit.objects.count(), 1)
        credit = StatementCredit.objects.get()
        self.assertEqual(credit.credit_card, CreditCard.objects.get())
        self.assertEqual(credit.amount, Decimal("120.00"))

    def test_perk_payload_accepts_null_value_and_is_idempotent(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        payload = {
            "data": [
                {
                    "id": "55424bce-93e7-4167-b48c-5bb981f5a2ea",
                    "perk_type": "lounge",
                    "perk_name": "Priority Pass Lounge Access",
                    "perk_value": None,
                    "perk_period": "unlimited",
                    "partner": "Priority Pass",
                    "details": "Enrollment required",
                }
            ]
        }

        import_perks_payload("american-express-gold-card", payload)
        import_perks_payload("american-express-gold-card", payload)

        self.assertEqual(Perk.objects.count(), 1)
        perk = Perk.objects.get()
        self.assertEqual(perk.credit_card, CreditCard.objects.get())
        self.assertIsNone(perk.value)

    def test_curated_import_supports_credits_and_perks(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        stats = import_curated_payload(
            {
                "data": [
                    {
                        "cardapi_slug": "american-express-gold-card",
                        "source_url": "https://www.americanexpress.com/example",
                        "verified_at": "2026-09-02",
                        "statement_credits": [
                            {
                                "source_key": "dining-credit-2026",
                                "name": "Dining Credit",
                                "amount": 120,
                                "period": "annual",
                            }
                        ],
                        "perks": [
                            {
                                "source_key": "lounge-access-2026",
                                "name": "Lounge Access",
                                "value": None,
                                "period": "annual",
                            }
                        ],
                    }
                ]
            }
        )

        self.assertEqual(stats["statement_credits_created"], 1)
        self.assertEqual(stats["perks_created"], 1)
        self.assertEqual(StatementCredit.objects.count(), 1)
        self.assertEqual(Perk.objects.count(), 1)

    def test_reviewed_schedule_and_offer_supersede_undated_cardapi_rows(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        import_curated_payload(
            {
                "data": [
                    {
                        "cardapi_slug": "american-express-gold-card",
                        "source_url": "https://www.americanexpress.com/example",
                        "verified_at": "2026-09-02",
                        "reward_rates": [
                            {
                                "source_key": "official-base",
                                "category_slug": "other",
                                "rate_multiplier": 1,
                                "rate_type": "points_per_dollar",
                                "is_base_rate": True,
                            }
                        ],
                        "signup_bonuses": [
                            {
                                "source_key": "public-offer-2026-09-02",
                                "offer_text": "Official public offer",
                            }
                        ],
                    }
                ]
            }
        )

        undated_api_payload = deepcopy(CARD_PAYLOAD)
        del undated_api_payload["data"][0]["updated_at"]
        import_cards_payload(undated_api_payload)

        card = CreditCard.objects.get()
        self.assertEqual(card.reward_rates.filter(is_active=True).count(), 1)
        self.assertEqual(
            card.reward_rates.get(is_active=True).source_key, "official-base"
        )
        self.assertEqual(card.signup_bonuses.filter(is_active=True).count(), 1)
        self.assertEqual(
            card.signup_bonuses.get(is_active=True).source_type,
            SignupBonus.SourceType.CURATED,
        )

    def test_coverage_report_marks_incomplete_base_rate(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))

        report = build_coverage_report(
            unavailable=("perks", "statement_credits")
        )

        card = report["cards"][0]
        self.assertFalse(card["recommendation_ready"])
        self.assertEqual(card["statuses"]["base_reward_rate"], "incomplete")
        self.assertEqual(card["statuses"]["perks"], "unavailable_on_plan")
        self.assertEqual(
            card["statuses"]["statement_credits"], "unavailable_on_plan"
        )

    def test_coverage_report_marks_core_complete_card_ready(self):
        payload = deepcopy(CARD_PAYLOAD)
        payload["data"][0]["reward_rates"][0]["is_base_rate"] = True
        import_cards_payload(payload)
        card = CreditCard.objects.get()
        program = RewardProgram.objects.create(
            code="coverage-points",
            name="Coverage Points",
            issuer=card.issuer,
            unit=RewardProgram.Unit.POINTS,
        )
        CardRewardProgram.objects.create(
            credit_card=card,
            reward_program=program,
        )
        card.signup_bonuses.update(reward_program=program)

        report = build_coverage_report()

        self.assertEqual(report["summary"]["recommendation_ready"], 1)
        self.assertEqual(
            report["cards"][0]["statuses"]["reward_program_mapping"],
            "present",
        )

    def test_coverage_report_flags_missing_reward_program_mapping(self):
        payload = deepcopy(CARD_PAYLOAD)
        payload["data"][0]["reward_rates"][0]["is_base_rate"] = True
        import_cards_payload(payload)

        card = build_coverage_report()["cards"][0]

        self.assertFalse(card["recommendation_ready"])
        self.assertEqual(card["statuses"]["reward_program_mapping"], "missing")

    def test_reward_program_import_classifies_program_and_links_bonus(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()

        import_reward_program_payload(
            {
                "programs": [
                    {
                        "code": "example-airline",
                        "name": "Example Airline",
                        "unit": "points",
                        "program_type": "airline",
                        "source_url": "https://example.com/program",
                        "verified_at": "2026-09-02",
                    }
                ],
                "memberships": [
                    {
                        "card_slug": card.local_slug,
                        "program_code": "example-airline",
                        "source_url": "https://example.com/card",
                        "verified_at": "2026-09-02",
                    }
                ],
            }
        )

        program = RewardProgram.objects.get(code="example-airline")
        self.assertEqual(program.program_type, RewardProgram.ProgramType.AIRLINE)
        self.assertEqual(card.signup_bonuses.get().reward_program, program)

    def test_coverage_command_supports_json_output(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        output = StringIO()

        call_command(
            "cardapi_coverage",
            format="json",
            unavailable=["perks", "statement_credits"],
            stdout=output,
        )

        self.assertIn('"recommendation_ready": 0', output.getvalue())
        self.assertIn('"unavailable_on_plan"', output.getvalue())

    def test_reward_match_requires_booking_details_when_rate_can_change(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        travel = RewardCategory.objects.get(slug="travel")
        hotels = RewardCategory.objects.get(slug="hotels")
        CCRewardRate.objects.create(
            credit_card=card,
            category=travel,
            source_key="portal",
            rate_multiplier=8,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            booking_channel=CCRewardRate.BookingChannel.ISSUER_PORTAL,
            booking_portal="Example Travel",
        )
        CCRewardRate.objects.create(
            credit_card=card,
            category=hotels,
            source_key="direct",
            rate_multiplier=4,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            booking_channel=CCRewardRate.BookingChannel.DIRECT,
        )

        result = match_reward_rate(card=card, category="hotels", amount=500)

        self.assertEqual(result.status, "needs_information")
        self.assertIn("booking_channel", result.missing_inputs)

    def test_reward_match_selects_direct_hotel_rule(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        hotels = RewardCategory.objects.get(slug="hotels")
        rate = CCRewardRate.objects.create(
            credit_card=card,
            category=hotels,
            source_key="direct",
            rate_multiplier=4,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            booking_channel=CCRewardRate.BookingChannel.DIRECT,
        )

        result = match_reward_rate(
            card=card,
            category="hotels",
            amount=500,
            booking_channel="direct",
        )

        self.assertEqual(result.status, "matched")
        self.assertEqual(result.reward_rate, rate)
        self.assertEqual(result.reward_amount, Decimal("2000"))
        self.assertEqual(result.reward_unit, "points")

    def test_reward_match_splits_purchase_at_cap(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        groceries = RewardCategory.objects.get(slug="groceries")
        rate = CCRewardRate.objects.create(
            credit_card=card,
            category=groceries,
            source_key="capped-groceries",
            rate_multiplier=4,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            cap_amount=100,
            cap_period=CCRewardRate.CapPeriod.ANNUAL,
            fallback_rate=1,
        )

        result = match_reward_rate(
            card=card,
            category="groceries",
            amount=20,
            category_spend_to_date=90,
        )

        self.assertEqual(result.status, "matched")
        self.assertEqual(result.reward_rate, rate)
        self.assertEqual(result.matched_amount, Decimal("10"))
        self.assertEqual(result.fallback_amount, Decimal("10"))
        self.assertEqual(result.reward_amount, Decimal("50"))

    def test_card_comparison_uses_cash_cpp_and_ranks_cards(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        points_card = CreditCard.objects.get()
        issuer = points_card.issuer
        cash_card = CreditCard.objects.create(
            local_slug="cash-card",
            cardapi_slug="cash-card",
            issuer=issuer,
            name="Cash Card",
        )
        dining = RewardCategory.objects.get(slug="dining")
        CCRewardRate.objects.create(
            credit_card=cash_card,
            category=dining,
            source_key="cash-dining",
            rate_multiplier=3,
            rate_type=CCRewardRate.RateType.PERCENT_CASHBACK,
        )
        program = RewardProgram.objects.create(
            code="test-points",
            name="Test Points",
            issuer=issuer,
            unit=RewardProgram.Unit.POINTS,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=points_card,
            reward_program=program,
            can_cash_redeem=True,
        )

        results = compare_cards(
            cards=[cash_card, points_card],
            category="dining",
            amount=100,
            valuation_strategy="cash",
            category_spend_to_date=0,
        )

        self.assertEqual(results[0].card, points_card)
        self.assertEqual(results[0].estimated_value, Decimal("4"))
        self.assertEqual(results[0].rank, 1)
        self.assertEqual(results[1].estimated_value, Decimal("3"))

    def test_companion_card_unlocks_transfer_valuation(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        source_card = CreditCard.objects.get()
        companion = CreditCard.objects.create(
            local_slug="companion",
            cardapi_slug="companion",
            issuer=source_card.issuer,
            name="Companion Card",
        )
        program = RewardProgram.objects.create(
            code="test-transfer",
            name="Test Transfer Points",
            issuer=source_card.issuer,
            unit=RewardProgram.Unit.POINTS,
        )
        CardRewardProgram.objects.create(
            credit_card=source_card,
            reward_program=program,
            can_transfer_partners=False,
            can_combine_rewards=True,
        )
        RewardProgramUnlock.objects.create(
            reward_program=program,
            source_card=source_card,
            required_card=companion,
            capability=RewardProgramUnlock.Capability.TRANSFER_PARTNERS,
            source_url="https://example.com/rewards",
            verified_at="2026-09-02",
        )

        without_companion = compare_cards(
            cards=[source_card],
            category="dining",
            amount=100,
            valuation_strategy="transfer",
            custom_cpp={"test-transfer": 2},
            category_spend_to_date=0,
        )[0]
        with_companion = compare_cards(
            cards=[source_card],
            owned_cards=[companion],
            category="dining",
            amount=100,
            valuation_strategy="transfer",
            custom_cpp={"test-transfer": 2},
            category_spend_to_date=0,
        )[0]

        self.assertIsNone(without_companion.estimated_value)
        self.assertEqual(with_companion.estimated_value, Decimal("8"))
        self.assertEqual(with_companion.unlocked_by, companion)

    def test_portfolio_assigns_spending_and_subtracts_recurring_fees(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        points_card = CreditCard.objects.get()
        points_card.annual_fee = 95
        points_card.save(update_fields=("annual_fee",))
        dining = RewardCategory.objects.get(slug="dining")
        issuer = points_card.issuer
        cash_card = CreditCard.objects.create(
            local_slug="cash-card", issuer=issuer, name="Cash Card", annual_fee=0
        )
        CCRewardRate.objects.create(
            credit_card=cash_card,
            category=dining,
            source_key="cash-dining",
            rate_multiplier=3,
            rate_type=CCRewardRate.RateType.PERCENT_CASHBACK,
        )
        program = RewardProgram.objects.create(
            code="portfolio-points",
            name="Portfolio Points",
            issuer=issuer,
            unit=RewardProgram.Unit.POINTS,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=points_card,
            reward_program=program,
            can_cash_redeem=True,
        )

        result = evaluate_portfolio(
            cards=[points_card, cash_card],
            spending={"dining": 10000},
        )

        self.assertEqual(result.allocations[0].comparison.card, points_card)
        self.assertEqual(result.estimated_reward_value, Decimal("400"))
        self.assertEqual(result.recurring_annual_fees, Decimal("95"))
        self.assertEqual(result.recurring_net_value, Decimal("305"))

    def test_portfolio_only_values_explicitly_usable_statement_credits(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        card.annual_fee = 325
        card.save(update_fields=("annual_fee",))
        credit = StatementCredit.objects.create(
            credit_card=card,
            name="Monthly Dining Credit",
            amount=10,
            period=StatementCredit.Period.MONTHLY,
            source_key="monthly-dining",
        )
        program = RewardProgram.objects.create(
            code="credit-points",
            name="Credit Points",
            issuer=card.issuer,
            unit=RewardProgram.Unit.POINTS,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=card,
            reward_program=program,
            can_cash_redeem=True,
        )

        result = evaluate_portfolio(
            cards=[card],
            spending={"dining": 1000},
            statement_credit_uses=[StatementCreditUse(credit, Decimal("0.5"))],
        )

        self.assertEqual(result.estimated_statement_credit_value, Decimal("60.0"))
        self.assertEqual(result.recurring_net_value, Decimal("-225.0"))

    def test_portfolio_annualizes_monthly_reward_cap(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        card.annual_fee = 0
        card.save(update_fields=("annual_fee",))
        rate = card.reward_rates.get()
        rate.cap_amount = 100
        rate.cap_period = CCRewardRate.CapPeriod.MONTHLY
        rate.fallback_rate = 1
        rate.save(update_fields=("cap_amount", "cap_period", "fallback_rate"))
        program = RewardProgram.objects.create(
            code="capped-points",
            name="Capped Points",
            issuer=card.issuer,
            unit=RewardProgram.Unit.POINTS,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=card,
            reward_program=program,
            can_cash_redeem=True,
        )

        result = evaluate_portfolio(cards=[card], spending={"dining": 2400})

        self.assertEqual(result.estimated_reward_value, Decimal("60"))
        self.assertIn("Periodic cap assumes spending is distributed across the year.", result.warnings)

    def test_candidate_analysis_ranks_incremental_value_after_fee(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        current = CreditCard.objects.get()
        current.annual_fee = 0
        current.save(update_fields=("annual_fee",))
        dining = RewardCategory.objects.get(slug="dining")
        candidate = CreditCard.objects.create(
            local_slug="candidate", issuer=current.issuer, name="Candidate", annual_fee=95
        )
        CCRewardRate.objects.create(
            credit_card=candidate,
            category=dining,
            source_key="candidate-dining",
            rate_multiplier=5,
            rate_type=CCRewardRate.RateType.PERCENT_CASHBACK,
        )
        program = RewardProgram.objects.create(
            code="baseline-points",
            name="Baseline Points",
            issuer=current.issuer,
            unit=RewardProgram.Unit.POINTS,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=current,
            reward_program=program,
            can_cash_redeem=True,
        )

        analysis = analyze_candidate_cards(
            current_cards=[current],
            candidates=[candidate],
            spending=[SpendingBucket("dining", Decimal("10000"))],
        )

        self.assertEqual(analysis.baseline.recurring_net_value, Decimal("400"))
        self.assertEqual(analysis.candidates[0].portfolio.recurring_net_value, Decimal("405"))
        self.assertEqual(analysis.candidates[0].incremental_recurring_value, Decimal("5"))
        self.assertEqual(analysis.candidates[0].rank, 1)

    def test_candidate_credit_is_excluded_from_baseline_and_included_with_card(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        current = CreditCard.objects.get()
        current.annual_fee = 0
        current.save(update_fields=("annual_fee",))
        candidate = CreditCard.objects.create(
            local_slug="credit-candidate",
            issuer=current.issuer,
            name="Credit Candidate",
            annual_fee=100,
        )
        dining = RewardCategory.objects.get(slug="dining")
        CCRewardRate.objects.create(
            credit_card=candidate,
            category=dining,
            source_key="credit-candidate-dining",
            rate_multiplier=4,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
        )
        program = RewardProgram.objects.create(
            code="shared-points",
            name="Shared Points",
            issuer=current.issuer,
            unit=RewardProgram.Unit.POINTS,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=current,
            reward_program=program,
            can_cash_redeem=True,
        )
        CardRewardProgram.objects.create(
            credit_card=candidate,
            reward_program=program,
            can_cash_redeem=True,
        )
        credit = StatementCredit.objects.create(
            credit_card=candidate,
            name="Candidate Annual Credit",
            amount=75,
            period=StatementCredit.Period.ANNUAL,
            source_key="candidate-credit",
        )

        analysis = analyze_candidate_cards(
            current_cards=[current],
            candidates=[candidate],
            spending={"dining": 1000},
            statement_credit_uses=[StatementCreditUse(credit, 1)],
        )

        self.assertEqual(analysis.baseline.estimated_statement_credit_value, Decimal("0"))
        self.assertEqual(
            analysis.candidates[0].portfolio.estimated_statement_credit_value,
            Decimal("75"),
        )

    def test_signup_bonus_adds_first_year_value_without_changing_recurring_value(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        current = CreditCard.objects.get()
        current.annual_fee = 0
        current.save(update_fields=("annual_fee",))
        program = RewardProgram.objects.create(
            code="welcome-points",
            name="Welcome Points",
            issuer=current.issuer,
            unit=RewardProgram.Unit.POINTS,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=current,
            reward_program=program,
            can_cash_redeem=True,
        )
        candidate = CreditCard.objects.create(
            local_slug="welcome-candidate",
            issuer=current.issuer,
            name="Welcome Candidate",
            annual_fee=95,
        )
        CardRewardProgram.objects.create(
            credit_card=candidate,
            reward_program=program,
            can_cash_redeem=True,
        )
        bonus = SignupBonus.objects.create(
            credit_card=candidate,
            reward_program=program,
            offer_text="Earn 60,000 points after spending $4,000 in three months.",
            bonus_amount=60000,
            bonus_unit=RewardProgram.Unit.POINTS,
            minimum_spend=4000,
            minimum_spend_months=3,
            source_key="welcome-60k",
            source_type=SignupBonus.SourceType.CURATED,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )

        analysis = analyze_candidate_cards(
            current_cards=[current],
            candidates=[candidate],
            spending={"dining": 1000},
            signup_bonus_uses=[
                SignupBonusUse(
                    bonus,
                    eligibility=BonusEligibility.ELIGIBLE,
                    can_meet_minimum_spend=True,
                )
            ],
        )
        result = analysis.candidates[0]

        self.assertEqual(result.signup_bonus.estimated_value, Decimal("600"))
        self.assertTrue(result.signup_bonus.is_included)
        self.assertEqual(result.incremental_recurring_value, Decimal("-95"))
        self.assertEqual(result.incremental_first_year_value, Decimal("505"))

    def test_unconfirmed_signup_bonus_is_shown_but_not_included(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        current = CreditCard.objects.get()
        current.annual_fee = 0
        current.save(update_fields=("annual_fee",))
        candidate = CreditCard.objects.create(
            local_slug="cash-welcome-candidate",
            issuer=current.issuer,
            name="Cash Welcome Candidate",
            annual_fee=95,
        )
        bonus = SignupBonus.objects.create(
            credit_card=candidate,
            offer_text="Earn $200 after spending $500 in three months.",
            bonus_amount=200,
            bonus_unit=RewardProgram.Unit.CASH,
            minimum_spend=500,
            minimum_spend_months=3,
            source_key="cash-welcome",
            source_type=SignupBonus.SourceType.CURATED,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )

        analysis = analyze_candidate_cards(
            current_cards=[current],
            candidates=[candidate],
            spending={"dining": 1000},
        )
        result = analysis.candidates[0]

        self.assertEqual(result.signup_bonus.signup_bonus, bonus)
        self.assertEqual(result.signup_bonus.estimated_value, Decimal("200"))
        self.assertFalse(result.signup_bonus.is_included)
        self.assertEqual(result.signup_bonus.included_value, Decimal("0"))
        self.assertIn(
            "Signup-bonus eligibility has not been confirmed.",
            result.signup_bonus.reasons,
        )

    def test_transfer_partner_import_is_idempotent_and_classifies_destination(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        source = RewardProgram.objects.create(
            code="source-points",
            name="Source Points",
            issuer=card.issuer,
            unit=RewardProgram.Unit.POINTS,
        )
        CardRewardProgram.objects.create(
            credit_card=card,
            reward_program=source,
            can_transfer_partners=True,
        )
        payload = {
            "programs": [
                {
                    "code": "destination-airline",
                    "name": "Destination Airline",
                    "unit": "miles",
                    "program_type": "airline",
                    "source_url": "https://example.com/program",
                    "verified_at": "2026-09-02",
                }
            ],
            "catalogs": [
                {
                    "source_program_code": "source-points",
                    "source_url": "https://example.com/transfers",
                    "verified_at": "2026-09-02",
                    "source_amount": 1000,
                    "destination_amount": 750,
                    "partners": [
                        {"destination_program_code": "destination-airline"}
                    ],
                }
            ],
        }

        first = import_transfer_partner_payload(payload)
        second = import_transfer_partner_payload(payload)

        self.assertEqual(first["routes_created"], 1)
        self.assertEqual(second["routes_created"], 0)
        self.assertEqual(RewardTransferRoute.objects.count(), 1)
        destination = RewardProgram.objects.get(code="destination-airline")
        self.assertEqual(destination.program_type, RewardProgram.ProgramType.AIRLINE)

        import_transfer_partner_payload(
            {
                "catalogs": [
                    {
                        "source_program_code": "source-points",
                        "source_url": "https://example.com/transfers",
                        "verified_at": "2026-09-02",
                        "partners": [],
                    }
                ]
            }
        )
        self.assertFalse(RewardTransferRoute.objects.get().is_active)

    def test_goal_match_supports_direct_and_transfer_access(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        source_card = CreditCard.objects.get()
        source = RewardProgram.objects.create(
            code="goal-source",
            name="Goal Source",
            issuer=source_card.issuer,
            unit=RewardProgram.Unit.POINTS,
        )
        target = RewardProgram.objects.create(
            code="goal-airline",
            name="Goal Airline",
            unit=RewardProgram.Unit.MILES,
            program_type=RewardProgram.ProgramType.AIRLINE,
        )
        CardRewardProgram.objects.create(
            credit_card=source_card,
            reward_program=source,
            can_transfer_partners=True,
        )
        direct_card = CreditCard.objects.create(
            local_slug="direct-goal-card",
            issuer=source_card.issuer,
            name="Direct Goal Card",
        )
        CardRewardProgram.objects.create(
            credit_card=direct_card,
            reward_program=target,
        )
        RewardTransferRoute.objects.create(
            source_key="goal-source-to-airline",
            source_program=source,
            destination_program=target,
            source_amount=1000,
            destination_amount=1000,
            source_url="https://example.com/transfers",
            verified_at="2026-09-02",
        )

        results = match_reward_goals(
            cards=[source_card, direct_card],
            goals=[RewardGoal((target,), "Fly Goal Airline")],
        )

        self.assertEqual(results[0].card, direct_card)
        self.assertEqual(results[0].goal_results[0].options[0].method, "direct_earn")
        transfer_result = next(result for result in results if result.card == source_card)
        self.assertEqual(transfer_result.goal_results[0].status, "matched")
        self.assertEqual(
            transfer_result.goal_results[0].options[0].conversion_ratio,
            Decimal("1"),
        )

    def test_goal_match_uses_companion_card_transfer_unlock(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        source_card = CreditCard.objects.get()
        companion = CreditCard.objects.create(
            local_slug="goal-companion",
            issuer=source_card.issuer,
            name="Goal Companion",
        )
        source = RewardProgram.objects.create(
            code="locked-source",
            name="Locked Source",
            issuer=source_card.issuer,
            unit=RewardProgram.Unit.POINTS,
        )
        target = RewardProgram.objects.create(
            code="locked-target",
            name="Locked Target",
            unit=RewardProgram.Unit.MILES,
            program_type=RewardProgram.ProgramType.AIRLINE,
        )
        CardRewardProgram.objects.create(
            credit_card=source_card,
            reward_program=source,
            can_transfer_partners=False,
        )
        RewardProgramUnlock.objects.create(
            reward_program=source,
            source_card=source_card,
            required_card=companion,
            capability=RewardProgramUnlock.Capability.TRANSFER_PARTNERS,
            source_url="https://example.com/unlock",
            verified_at="2026-09-02",
        )
        RewardTransferRoute.objects.create(
            source_key="locked-route",
            source_program=source,
            destination_program=target,
            source_amount=1000,
            destination_amount=1000,
            source_url="https://example.com/route",
            verified_at="2026-09-02",
        )

        without = match_reward_goals(
            cards=[source_card],
            goals=[RewardGoal((target,), "Locked goal")],
        )[0]
        with_companion = match_reward_goals(
            cards=[source_card],
            owned_cards=[companion],
            goals=[RewardGoal((target,), "Locked goal")],
        )[0]

        self.assertEqual(without.goal_results[0].status, "unavailable")
        self.assertEqual(with_companion.goal_results[0].status, "matched")
        self.assertEqual(
            with_companion.goal_results[0].options[0].method,
            "portfolio_unlock",
        )

    def test_goal_match_requests_open_date_for_card_specific_ratio(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        card = CreditCard.objects.get()
        source = RewardProgram.objects.create(
            code="cohort-source",
            name="Cohort Source",
            issuer=card.issuer,
            unit=RewardProgram.Unit.POINTS,
        )
        target = RewardProgram.objects.create(
            code="cohort-hotel",
            name="Cohort Hotel",
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.HOTEL,
        )
        CardRewardProgram.objects.create(
            credit_card=card,
            reward_program=source,
            can_transfer_partners=True,
        )
        common = {
            "source_program": source,
            "destination_program": target,
            "source_amount": 1000,
            "source_url": "https://example.com/cohorts",
            "verified_at": "2026-09-02",
        }
        RewardTransferRoute.objects.create(
            source_key="cohort-general", destination_amount=1000, **common
        )
        RewardTransferRoute.objects.create(
            source_key="cohort-new",
            destination_amount=750,
            eligible_card=card,
            account_opened_on_or_after="2026-06-15",
            **common,
        )

        unknown = match_reward_goals(
            cards=[card],
            goals=[RewardGoal((target,), "Hotel goal")],
            as_of=date(2026, 9, 2),
        )[0]
        known = match_reward_goals(
            cards=[card],
            goals=[RewardGoal((target,), "Hotel goal")],
            account_opened_dates={card.pk: date(2026, 7, 1)},
            as_of=date(2026, 9, 2),
        )[0]

        self.assertEqual(unknown.goal_results[0].status, "needs_information")
        self.assertIn(
            f"account_opened_on:{card.pk}",
            unknown.goal_results[0].missing_inputs,
        )
        self.assertEqual(
            known.goal_results[0].options[0].conversion_ratio,
            Decimal("0.75"),
        )

    def test_candidate_analysis_reports_incremental_goal_fit_separately(self):
        import_cards_payload(deepcopy(CARD_PAYLOAD))
        current = CreditCard.objects.get()
        current.annual_fee = 0
        current.save(update_fields=("annual_fee",))
        target = RewardProgram.objects.create(
            code="candidate-goal",
            name="Candidate Goal Airline",
            unit=RewardProgram.Unit.MILES,
            program_type=RewardProgram.ProgramType.AIRLINE,
        )
        candidate = CreditCard.objects.create(
            local_slug="goal-fit-candidate",
            issuer=current.issuer,
            name="Goal Fit Candidate",
            annual_fee=0,
        )
        CardRewardProgram.objects.create(
            credit_card=candidate,
            reward_program=target,
        )

        result = analyze_candidate_cards(
            current_cards=[current],
            candidates=[candidate],
            spending={"dining": 1000},
            reward_goals=[RewardGoal((target,), "Fly the target airline", 3)],
        ).candidates[0]

        self.assertEqual(result.incremental_goal_priority, Decimal("3"))
        self.assertEqual(len(result.goal_summary.covered_goals), 1)
        self.assertEqual(result.goal_rank, 1)


class CardCatalogAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.issuer = Issuer.objects.create(
            slug="catalog-bank",
            name="Catalog Bank",
            country="US",
            is_active=True,
        )
        self.card = CreditCard.objects.create(
            local_slug="catalog-card",
            cardapi_slug="cardapi-catalog-card",
            issuer=self.issuer,
            name="Catalog Rewards Card",
            network=CreditCard.Network.VISA,
            card_type=CreditCard.CardType.PERSONAL,
            annual_fee=95,
            foreign_transaction_fee=0,
            reward_currency="CAT",
            reward_currency_name="Catalog Points",
            product_url="https://example.com/catalog-card",
            official_page_verified_at="2026-09-02",
        )
        self.category = RewardCategory.objects.create(
            slug="catalog-dining", category="Dining"
        )
        self.rate = CCRewardRate.objects.create(
            credit_card=self.card,
            category=self.category,
            rate_multiplier=3,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            source_key="catalog-dining-rate",
            source_url="https://example.com/internal-source",
            verified_at="2026-09-02",
        )
        self.program = RewardProgram.objects.create(
            code="catalog-points",
            name="Catalog Points",
            issuer=self.issuer,
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.ISSUER,
        )
        CardRewardProgram.objects.create(
            credit_card=self.card,
            reward_program=self.program,
            can_transfer_partners=True,
        )
        self.destination = RewardProgram.objects.create(
            code="catalog-airline",
            name="Catalog Airline",
            unit=RewardProgram.Unit.MILES,
            program_type=RewardProgram.ProgramType.AIRLINE,
        )
        RewardTransferRoute.objects.create(
            source_key="catalog-transfer",
            source_program=self.program,
            destination_program=self.destination,
            source_amount=1000,
            destination_amount=1000,
            source_url="https://example.com/internal-transfer-source",
            verified_at="2026-09-02",
        )
        SignupBonus.objects.create(
            credit_card=self.card,
            reward_program=self.program,
            offer_text="Earn 10,000 points.",
            bonus_amount=10000,
            bonus_unit=RewardProgram.Unit.POINTS,
            source_key="catalog-bonus",
            source_type=SignupBonus.SourceType.CURATED,
            source_url="https://example.com/internal-bonus-source",
            verified_at="2026-09-02",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )
        StatementCredit.objects.create(
            credit_card=self.card,
            name="Catalog Credit",
            amount=100,
            period=StatementCredit.Period.ANNUAL,
            source_key="catalog-credit",
        )
        Perk.objects.create(
            credit_card=self.card,
            name="Catalog Protection",
            perk_type="protection",
            source_key="catalog-perk",
        )
        self.discontinued = CreditCard.objects.create(
            local_slug="legacy-card",
            issuer=self.issuer,
            name="Legacy Card",
            is_discontinued=True,
        )

    def test_card_list_is_public_paginated_and_compact(self):
        response = self.client.get(reverse("cardapi:card-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        card = response.data["results"][0]
        self.assertEqual(card["slug"], "catalog-card")
        self.assertEqual(card["issuer"]["slug"], "catalog-bank")
        self.assertNotIn("reward_rates", card)
        self.assertNotIn("cardapi_id", card)

    def test_card_list_filters_and_can_include_discontinued(self):
        response = self.client.get(
            reverse("cardapi:card-list"),
            {
                "issuer": "catalog-bank",
                "card_type": "personal",
                "max_annual_fee": "100",
                "reward_category": "catalog-dining",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["slug"] for row in response.data["results"]], ["catalog-card"])

        response = self.client.get(
            reverse("cardapi:card-list"), {"include_discontinued": "true"}
        )
        self.assertEqual(response.data["count"], 2)

    def test_card_list_rejects_invalid_filters(self):
        invalid_fee = self.client.get(
            reverse("cardapi:card-list"), {"max_annual_fee": "free"}
        )
        invalid_type = self.client.get(
            reverse("cardapi:card-list"), {"card_type": "consumer"}
        )
        invalid_boolean = self.client.get(
            reverse("cardapi:card-list"), {"include_discontinued": "sometimes"}
        )
        invalid_category = self.client.get(
            reverse("cardapi:card-list"), {"reward_category": "not-real"}
        )

        self.assertEqual(invalid_fee.status_code, 400)
        self.assertEqual(invalid_type.status_code, 400)
        self.assertEqual(invalid_boolean.status_code, 400)
        self.assertEqual(invalid_category.status_code, 400)

        for non_finite in ("NaN", "Infinity", "-Infinity"):
            response = self.client.get(
                reverse("cardapi:card-list"),
                {"max_annual_fee": non_finite},
            )
            self.assertEqual(response.status_code, 400)

    def test_card_detail_returns_only_active_related_records(self):
        CCRewardRate.objects.create(
            credit_card=self.card,
            category=self.category,
            rate_multiplier=9,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            source_key="inactive-rate",
            is_active=False,
        )

        response = self.client.get(
            reverse("cardapi:card-detail", kwargs={"slug": self.card.local_slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["slug"], "catalog-card")
        self.assertEqual(len(response.data["reward_rates"]), 1)
        self.assertEqual(len(response.data["signup_bonuses"]), 1)
        self.assertEqual(len(response.data["statement_credits"]), 1)
        self.assertEqual(len(response.data["perks"]), 1)
        self.assertEqual(len(response.data["transfer_partners"]), 1)
        self.assertEqual(
            response.data["transfer_partners"][0]["destination_program"]["code"],
            "catalog-airline",
        )
        self.assertNotIn("source_key", response.data["reward_rates"][0])
        self.assertNotIn("source_url", response.data["reward_rates"][0])

    def test_discontinued_card_remains_available_by_direct_slug(self):
        response = self.client.get(
            reverse(
                "cardapi:card-detail",
                kwargs={"slug": self.discontinued.local_slug},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_discontinued"])

    def test_unknown_card_returns_not_found(self):
        response = self.client.get(
            reverse("cardapi:card-detail", kwargs={"slug": "not-a-card"})
        )

        self.assertEqual(response.status_code, 404)


class CatalogMetadataAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.active_issuer = Issuer.objects.create(
            slug="active-bank", name="Active Bank", country="US"
        )
        CreditCard.objects.create(
            local_slug="active-bank-card",
            issuer=self.active_issuer,
            name="Active Bank Card",
        )
        CreditCard.objects.create(
            local_slug="active-bank-legacy-card",
            issuer=self.active_issuer,
            name="Active Bank Legacy Card",
            is_discontinued=True,
        )
        discontinued_issuer = Issuer.objects.create(
            slug="legacy-bank", name="Legacy Bank", country="US"
        )
        CreditCard.objects.create(
            local_slug="legacy-bank-card",
            issuer=discontinued_issuer,
            name="Legacy Bank Card",
            is_discontinued=True,
        )
        inactive_issuer = Issuer.objects.create(
            slug="inactive-bank", name="Inactive Bank", country="US", is_active=False
        )
        CreditCard.objects.create(
            local_slug="inactive-bank-card",
            issuer=inactive_issuer,
            name="Inactive Bank Card",
        )

        self.travel = RewardCategory.objects.create(
            slug="metadata-travel", category="Metadata Travel"
        )
        RewardCategory.objects.create(
            slug="metadata-flights", category="Metadata Flights", parent=self.travel
        )
        RewardCategory.objects.create(
            slug="inactive-travel-child",
            category="Inactive Travel Child",
            parent=self.travel,
            is_active=False,
        )
        RewardCategory.objects.create(
            slug="internal-category",
            category="Internal Category",
            is_user_facing=False,
        )
        RewardCategory.objects.create(
            slug="inactive-category",
            category="Inactive Category",
            is_active=False,
        )
        RewardProgram.objects.create(
            code="metadata-airline",
            name="Metadata Airline",
            unit=RewardProgram.Unit.MILES,
            program_type=RewardProgram.ProgramType.AIRLINE,
        )
        RewardProgram.objects.create(
            code="metadata-hotel",
            name="Metadata Hotel",
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.HOTEL,
        )
        RewardProgram.objects.create(
            code="metadata-inactive-program",
            name="Metadata Inactive Program",
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.ISSUER,
            is_active=False,
        )

    def test_issuer_list_is_public_unpaginated_and_counts_active_cards(self):
        response = self.client.get(reverse("cardapi:issuer-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "active-bank")
        self.assertEqual(response.data[0]["active_card_count"], 1)

    def test_reward_categories_are_public_hierarchical_and_user_facing(self):
        response = self.client.get(reverse("cardapi:reward-category-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        categories = {row["slug"]: row for row in response.data}
        self.assertIn("metadata-travel", categories)
        self.assertNotIn("internal-category", categories)
        self.assertNotIn("inactive-category", categories)
        travel = categories["metadata-travel"]
        self.assertEqual(travel["slug"], "metadata-travel")
        self.assertIsNone(travel["parent_slug"])
        self.assertEqual(
            travel["children"],
            [
                {
                    "slug": "metadata-flights",
                    "name": "Metadata Flights",
                    "parent_slug": "metadata-travel",
                }
            ],
        )

    def test_reward_programs_are_public_and_exclude_inactive_programs(self):
        response = self.client.get(reverse("cardapi:reward-program-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(
            [row["code"] for row in response.data],
            ["metadata-airline", "metadata-hotel"],
        )
        self.assertEqual(
            set(response.data[0]),
            {"code", "name", "unit", "program_type"},
        )

    def test_reward_programs_support_program_type_filter(self):
        response = self.client.get(
            reverse("cardapi:reward-program-list"),
            {"program_type": RewardProgram.ProgramType.HOTEL},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["code"] for row in response.data],
            ["metadata-hotel"],
        )

        invalid = self.client.get(
            reverse("cardapi:reward-program-list"),
            {"program_type": "not-a-program-type"},
        )
        self.assertEqual(invalid.status_code, 400)


class CardComparisonAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="comparison@example.com",
            password="comparison-test-password",
        )
        self.issuer = Issuer.objects.create(
            slug="comparison-bank", name="Comparison Bank", country="US"
        )
        self.category = RewardCategory.objects.create(
            slug="comparison-dining", category="Comparison Dining"
        )
        self.points_card = CreditCard.objects.create(
            local_slug="comparison-points-card",
            issuer=self.issuer,
            name="Comparison Points Card",
            annual_fee=0,
        )
        self.cash_card = CreditCard.objects.create(
            local_slug="comparison-cash-card",
            issuer=self.issuer,
            name="Comparison Cash Card",
            annual_fee=0,
        )
        CCRewardRate.objects.create(
            credit_card=self.points_card,
            category=self.category,
            rate_multiplier=4,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            source_key="comparison-points-rate",
        )
        CCRewardRate.objects.create(
            credit_card=self.cash_card,
            category=self.category,
            rate_multiplier=3,
            rate_type=CCRewardRate.RateType.PERCENT_CASHBACK,
            source_key="comparison-cash-rate",
        )
        self.program = RewardProgram.objects.create(
            code="comparison-points",
            name="Comparison Points",
            issuer=self.issuer,
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.ISSUER,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=self.points_card,
            reward_program=self.program,
            can_cash_redeem=True,
        )
        self.payload = {
            "card_slugs": [
                self.cash_card.local_slug,
                self.points_card.local_slug,
            ],
            "category_slug": self.category.slug,
            "amount": "100.00",
            "valuation_strategy": "cash",
        }

    def test_comparison_requires_authentication(self):
        response = self.client.post(
            reverse("cardapi:card-compare"), self.payload, format="json"
        )

        self.assertEqual(response.status_code, 401)

    def test_comparison_returns_ranked_defensible_values(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("cardapi:card-compare"), self.payload, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["category"]["slug"], self.category.slug)
        self.assertEqual(response.data["amount"], Decimal("100.00"))
        self.assertEqual(len(response.data["results"]), 2)
        best = response.data["results"][0]
        self.assertEqual(best["card"]["slug"], self.points_card.local_slug)
        self.assertEqual(best["rank"], 1)
        self.assertEqual(best["match_status"], "matched")
        self.assertEqual(best["reward_amount"], "400.0000")
        self.assertEqual(best["estimated_value"], "4.0000")
        self.assertEqual(best["effective_return_percent"], "4.0000")
        self.assertNotIn("cardapi_id", best["card"])
        self.assertNotIn("source_key", best["matched_reward_rate"])

    def test_comparison_reports_missing_purchase_context(self):
        self.client.force_authenticate(self.user)
        rate = self.points_card.reward_rates.get()
        rate.cap_amount = 1000
        rate.cap_period = CCRewardRate.CapPeriod.ANNUAL
        rate.fallback_rate = 1
        rate.save(update_fields=("cap_amount", "cap_period", "fallback_rate"))

        response = self.client.post(
            reverse("cardapi:card-compare"), self.payload, format="json"
        )

        self.assertEqual(response.status_code, 200)
        result = next(
            row
            for row in response.data["results"]
            if row["card"]["slug"] == self.points_card.local_slug
        )
        self.assertEqual(result["match_status"], "needs_information")
        self.assertIsNone(result["rank"])
        self.assertEqual(result["missing_inputs"], ["category_spend_to_date"])

    def test_comparison_validates_cards_category_and_custom_values(self):
        self.client.force_authenticate(self.user)
        duplicate = {**self.payload, "card_slugs": [self.cash_card.local_slug] * 2}
        unknown_card = {
            **self.payload,
            "card_slugs": [self.cash_card.local_slug, "unknown-card"],
        }
        unknown_category = {**self.payload, "category_slug": "unknown-category"}
        misplaced_custom_value = {
            **self.payload,
            "custom_cpp": {self.program.code: "2.0"},
        }

        self.assertEqual(
            self.client.post(
                reverse("cardapi:card-compare"), duplicate, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                reverse("cardapi:card-compare"), unknown_card, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                reverse("cardapi:card-compare"), unknown_category, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                reverse("cardapi:card-compare"),
                misplaced_custom_value,
                format="json",
            ).status_code,
            400,
        )

    def test_owned_card_can_unlock_transfer_valuation(self):
        self.client.force_authenticate(self.user)
        companion = CreditCard.objects.create(
            local_slug="comparison-companion-card",
            issuer=self.issuer,
            name="Comparison Companion Card",
        )
        membership = self.points_card.reward_program_memberships.get()
        membership.can_cash_redeem = False
        membership.can_combine_rewards = True
        membership.save(update_fields=("can_cash_redeem", "can_combine_rewards"))
        RewardProgramUnlock.objects.create(
            reward_program=self.program,
            source_card=self.points_card,
            required_card=companion,
            capability=RewardProgramUnlock.Capability.TRANSFER_PARTNERS,
            source_url="https://example.com/unlock",
            verified_at="2026-09-02",
        )
        payload = {
            **self.payload,
            "owned_card_slugs": [companion.local_slug],
            "valuation_strategy": "transfer",
            "custom_cpp": {self.program.code: "2.0"},
        }

        response = self.client.post(
            reverse("cardapi:card-compare"), payload, format="json"
        )

        self.assertEqual(response.status_code, 200)
        result = next(
            row
            for row in response.data["results"]
            if row["card"]["slug"] == self.points_card.local_slug
        )
        self.assertEqual(result["estimated_value"], "8.0000")
        self.assertEqual(result["unlocked_by"]["slug"], companion.local_slug)


class PortfolioEvaluationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="portfolio@example.com",
            password="portfolio-test-password",
        )
        self.issuer = Issuer.objects.create(
            slug="portfolio-api-bank", name="Portfolio API Bank", country="US"
        )
        self.category = RewardCategory.objects.create(
            slug="portfolio-api-dining", category="Portfolio API Dining"
        )
        self.points_card = CreditCard.objects.create(
            local_slug="portfolio-api-points-card",
            issuer=self.issuer,
            name="Portfolio API Points Card",
            annual_fee=95,
            annual_fee_waived_first_year=True,
        )
        self.cash_card = CreditCard.objects.create(
            local_slug="portfolio-api-cash-card",
            issuer=self.issuer,
            name="Portfolio API Cash Card",
            annual_fee=0,
        )
        CCRewardRate.objects.create(
            credit_card=self.points_card,
            category=self.category,
            rate_multiplier=4,
            rate_type=CCRewardRate.RateType.POINTS_PER_DOLLAR,
            source_key="portfolio-api-points-rate",
        )
        CCRewardRate.objects.create(
            credit_card=self.cash_card,
            category=self.category,
            rate_multiplier=3,
            rate_type=CCRewardRate.RateType.PERCENT_CASHBACK,
            source_key="portfolio-api-cash-rate",
        )
        program = RewardProgram.objects.create(
            code="portfolio-api-points",
            name="Portfolio API Points",
            issuer=self.issuer,
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.ISSUER,
            cash_value_cpp=1,
        )
        CardRewardProgram.objects.create(
            credit_card=self.points_card,
            reward_program=program,
            can_cash_redeem=True,
        )
        self.credit = StatementCredit.objects.create(
            credit_card=self.cash_card,
            name="Monthly Portfolio Credit",
            amount=10,
            period=StatementCredit.Period.MONTHLY,
            source_key="monthly-portfolio-credit",
        )
        Perk.objects.create(
            credit_card=self.points_card,
            name="Unvalued Portfolio Perk",
            source_key="unvalued-portfolio-perk",
        )
        self.payload = {
            "card_slugs": [
                self.points_card.local_slug,
                self.cash_card.local_slug,
            ],
            "spending": [
                {
                    "category_slug": self.category.slug,
                    "annual_amount": "10000.00",
                }
            ],
            "valuation_strategy": "cash",
            "statement_credit_uses": [
                {
                    "card_slug": self.cash_card.local_slug,
                    "credit_name": self.credit.name,
                    "utilization": "0.5000",
                }
            ],
        }

    def test_portfolio_evaluation_requires_authentication(self):
        response = self.client.post(
            reverse("cardapi:portfolio-evaluate"), self.payload, format="json"
        )

        self.assertEqual(response.status_code, 401)

    def test_portfolio_evaluation_returns_allocations_fees_and_credits(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("cardapi:portfolio-evaluate"), self.payload, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["annual_spend"], "10000.00")
        self.assertEqual(response.data["estimated_reward_value"], "400.0000")
        self.assertEqual(
            response.data["estimated_statement_credit_value"], "60.0000"
        )
        self.assertEqual(response.data["recurring_annual_fees"], "95.00")
        self.assertEqual(response.data["first_year_annual_fees"], "0.00")
        self.assertEqual(response.data["recurring_net_value"], "365.0000")
        self.assertEqual(
            response.data["first_year_net_value_before_signup_bonus"],
            "460.0000",
        )
        self.assertEqual(response.data["unvalued_perk_count"], 1)
        self.assertEqual(len(response.data["allocations"]), 1)
        self.assertEqual(
            response.data["allocations"][0]["comparison"]["card"]["slug"],
            self.points_card.local_slug,
        )
        self.assertEqual(
            response.data["credits_used"][0]["credit_name"], self.credit.name
        )

    def test_portfolio_evaluation_reports_unresolved_spending(self):
        self.client.force_authenticate(self.user)
        unmatched = RewardCategory.objects.create(
            slug="portfolio-api-unmatched", category="Portfolio API Unmatched"
        )
        payload = {
            **self.payload,
            "spending": [
                {
                    "category_slug": unmatched.slug,
                    "annual_amount": "500.00",
                }
            ],
            "statement_credit_uses": [],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-evaluate"), payload, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["recurring_net_value"])
        self.assertEqual(len(response.data["unresolved_spending"]), 1)
        self.assertEqual(
            response.data["unresolved_spending"][0]["category_slug"],
            unmatched.slug,
        )
        self.assertIn(
            "Net value is unavailable because some spending could not be valued.",
            response.data["warnings"],
        )

    def test_portfolio_evaluation_validates_references(self):
        self.client.force_authenticate(self.user)
        unknown_card = {
            **self.payload,
            "card_slugs": ["unknown-card"],
            "statement_credit_uses": [],
        }
        unknown_category = {
            **self.payload,
            "spending": [
                {"category_slug": "unknown-category", "annual_amount": "100"}
            ],
        }
        credit_outside_portfolio = {
            **self.payload,
            "card_slugs": [self.points_card.local_slug],
        }
        unknown_credit = deepcopy(self.payload)
        unknown_credit["statement_credit_uses"][0]["credit_name"] = "Not a credit"

        for invalid_payload in (
            unknown_card,
            unknown_category,
            credit_outside_portfolio,
            unknown_credit,
        ):
            response = self.client.post(
                reverse("cardapi:portfolio-evaluate"),
                invalid_payload,
                format="json",
            )
            self.assertEqual(response.status_code, 400)

    def test_candidate_analysis_requires_authentication(self):
        payload = {
            "current_card_slugs": [self.cash_card.local_slug],
            "candidate_card_slugs": [self.points_card.local_slug],
            "spending": self.payload["spending"],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-analyze-candidates"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_candidate_analysis_separates_recurring_and_first_year_value(self):
        self.client.force_authenticate(self.user)
        bonus = SignupBonus.objects.create(
            credit_card=self.points_card,
            offer_text="Earn $100 after spending $500 in three months.",
            bonus_amount=100,
            bonus_unit=RewardProgram.Unit.CASH,
            minimum_spend=500,
            minimum_spend_months=3,
            source_key="portfolio-api-public-offer",
            source_type=SignupBonus.SourceType.CURATED,
            source_url="https://example.com/offer",
            verified_at="2026-09-03",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )
        payload = {
            "current_card_slugs": [self.cash_card.local_slug],
            "candidate_card_slugs": [self.points_card.local_slug],
            "spending": self.payload["spending"],
            "valuation_strategy": "cash",
            "statement_credit_uses": self.payload["statement_credit_uses"],
            "signup_bonus_uses": [
                {
                    "card_slug": self.points_card.local_slug,
                    "eligibility": "eligible",
                    "can_meet_minimum_spend": True,
                }
            ],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-analyze-candidates"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["baseline"]["recurring_net_value"], "360.0000")
        self.assertEqual(len(response.data["candidates"]), 1)
        candidate = response.data["candidates"][0]
        self.assertEqual(candidate["candidate"]["slug"], self.points_card.local_slug)
        self.assertEqual(candidate["incremental_recurring_value"], "5.0000")
        self.assertEqual(candidate["rank"], 1)
        self.assertEqual(candidate["signup_bonus"]["estimated_value"], "100.0000")
        self.assertEqual(candidate["signup_bonus"]["included_value"], "100.0000")
        self.assertTrue(candidate["signup_bonus"]["is_included"])
        self.assertEqual(candidate["first_year_net_value"], "560.0000")
        self.assertEqual(candidate["incremental_first_year_value"], "200.0000")
        self.assertEqual(candidate["first_year_rank"], 1)
        self.assertEqual(candidate["signup_bonus"]["signup_bonus"]["offer_text"], bonus.offer_text)

    def test_candidate_analysis_does_not_assume_bonus_eligibility(self):
        self.client.force_authenticate(self.user)
        SignupBonus.objects.create(
            credit_card=self.points_card,
            offer_text="Earn $100 after spending $500 in three months.",
            bonus_amount=100,
            bonus_unit=RewardProgram.Unit.CASH,
            minimum_spend=500,
            minimum_spend_months=3,
            source_key="portfolio-api-unconfirmed-offer",
            source_type=SignupBonus.SourceType.CURATED,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )
        payload = {
            "current_card_slugs": [self.cash_card.local_slug],
            "candidate_card_slugs": [self.points_card.local_slug],
            "spending": self.payload["spending"],
            "valuation_strategy": "cash",
            "statement_credit_uses": self.payload["statement_credit_uses"],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-analyze-candidates"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        bonus = response.data["candidates"][0]["signup_bonus"]
        self.assertEqual(bonus["estimated_value"], "100.0000")
        self.assertEqual(bonus["included_value"], "0.0000")
        self.assertFalse(bonus["is_included"])
        self.assertIn(
            "Signup-bonus eligibility has not been confirmed.", bonus["reasons"]
        )

    def test_candidate_analysis_supports_an_empty_current_portfolio(self):
        self.client.force_authenticate(self.user)
        payload = {
            "current_card_slugs": [],
            "candidate_card_slugs": [self.cash_card.local_slug],
            "spending": self.payload["spending"],
            "valuation_strategy": "cash",
        }

        response = self.client.post(
            reverse("cardapi:portfolio-analyze-candidates"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["baseline"]["recurring_net_value"], "0.0000")
        self.assertEqual(
            response.data["candidates"][0]["incremental_recurring_value"],
            "300.0000",
        )

    def test_candidate_analysis_rejects_invalid_relationships(self):
        self.client.force_authenticate(self.user)
        base = {
            "current_card_slugs": [self.cash_card.local_slug],
            "candidate_card_slugs": [self.points_card.local_slug],
            "spending": self.payload["spending"],
        }
        overlap = {
            **base,
            "candidate_card_slugs": [self.cash_card.local_slug],
        }
        discontinued = CreditCard.objects.create(
            local_slug="portfolio-api-discontinued",
            issuer=self.issuer,
            name="Portfolio API Discontinued",
            is_discontinued=True,
        )
        discontinued_candidate = {
            **base,
            "candidate_card_slugs": [discontinued.local_slug],
        }
        bonus_for_current_card = {
            **base,
            "signup_bonus_uses": [
                {
                    "card_slug": self.cash_card.local_slug,
                    "eligibility": "eligible",
                    "can_meet_minimum_spend": True,
                }
            ],
        }

        for invalid_payload in (
            overlap,
            discontinued_candidate,
            bonus_for_current_card,
        ):
            response = self.client.post(
                reverse("cardapi:portfolio-analyze-candidates"),
                invalid_payload,
                format="json",
            )
            self.assertEqual(response.status_code, 400)


class RewardGoalMatchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="goal-api@example.com",
            password="test-password",
        )
        self.issuer = Issuer.objects.create(
            slug="goal-api-bank",
            name="Goal API Bank",
            country="US",
        )
        self.transfer_card = CreditCard.objects.create(
            local_slug="goal-api-transfer-card",
            issuer=self.issuer,
            name="Goal API Transfer Card",
        )
        self.flex_card = CreditCard.objects.create(
            local_slug="goal-api-flex-card",
            issuer=self.issuer,
            name="Goal API Flex Card",
        )
        self.unlock_card = CreditCard.objects.create(
            local_slug="goal-api-unlock-card",
            issuer=self.issuer,
            name="Goal API Unlock Card",
        )
        self.source_program = RewardProgram.objects.create(
            code="goal-api-points",
            name="Goal API Points",
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.ISSUER,
        )
        self.destination = RewardProgram.objects.create(
            code="goal-api-airline",
            name="Goal API Airline",
            unit=RewardProgram.Unit.MILES,
            program_type=RewardProgram.ProgramType.AIRLINE,
        )
        CardRewardProgram.objects.create(
            credit_card=self.transfer_card,
            reward_program=self.source_program,
            can_transfer_partners=True,
        )
        CardRewardProgram.objects.create(
            credit_card=self.flex_card,
            reward_program=self.source_program,
            can_combine_rewards=True,
        )
        RewardProgramUnlock.objects.create(
            reward_program=self.source_program,
            source_card=self.flex_card,
            required_card=self.unlock_card,
            capability=RewardProgramUnlock.Capability.TRANSFER_PARTNERS,
            source_url="https://example.com/unlock",
            verified_at=date(2026, 9, 1),
        )
        RewardTransferRoute.objects.create(
            source_key="goal-api-standard-route",
            source_program=self.source_program,
            destination_program=self.destination,
            source_amount=1,
            destination_amount=1,
            source_url="https://example.com/transfer",
            verified_at=date(2026, 9, 1),
        )
        self.payload = {
            "card_slugs": [
                self.flex_card.local_slug,
                self.transfer_card.local_slug,
            ],
            "owned_card_slugs": [self.unlock_card.local_slug],
            "goals": [
                {
                    "label": "Fly with Goal API Airline",
                    "program_codes": [self.destination.code],
                    "priority": "2.5",
                }
            ],
            "as_of": "2026-09-03",
        }

    def test_goal_matching_requires_authentication(self):
        response = self.client.post(
            reverse("cardapi:reward-goal-match"),
            self.payload,
            format="json",
        )

        self.assertIn(response.status_code, (401, 403))

    def test_goal_matching_ranks_and_reports_portfolio_unlocks(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("cardapi:reward-goal-match"),
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["as_of"], "2026-09-03")
        self.assertEqual(len(response.data["cards"]), 2)
        results_by_slug = {
            item["card"]["slug"]: item for item in response.data["cards"]
        }
        flex_result = results_by_slug[self.flex_card.local_slug]
        self.assertEqual(flex_result["covered_priority"], "2.5000")
        self.assertEqual(
            flex_result["goal_results"][0]["options"][0]["method"],
            "portfolio_unlock",
        )
        self.assertEqual(
            flex_result["goal_results"][0]["options"][0]["access_card"]["slug"],
            self.unlock_card.local_slug,
        )
        self.assertEqual(
            response.data["portfolio"]["covered_goals"][0]["label"],
            "Fly with Goal API Airline",
        )
        self.assertEqual(response.data["portfolio"]["covered_priority"], "2.5000")

    def test_goal_matching_reports_slug_for_missing_cohort_date(self):
        RewardTransferRoute.objects.filter(
            source_key="goal-api-standard-route"
        ).delete()
        for source_key, source_amount, destination_amount, date_fields in (
            (
                "goal-api-old-cohort",
                1,
                1,
                {"account_opened_before": date(2025, 1, 1)},
            ),
            (
                "goal-api-new-cohort",
                4,
                3,
                {"account_opened_on_or_after": date(2025, 1, 1)},
            ),
        ):
            RewardTransferRoute.objects.create(
                source_key=source_key,
                source_program=self.source_program,
                destination_program=self.destination,
                eligible_card=self.transfer_card,
                source_amount=source_amount,
                destination_amount=destination_amount,
                source_url="https://example.com/cohort",
                verified_at=date(2026, 9, 1),
                **date_fields,
            )
        self.client.force_authenticate(self.user)
        payload = deepcopy(self.payload)
        payload["card_slugs"] = [self.transfer_card.local_slug]
        payload["owned_card_slugs"] = []

        response = self.client.post(
            reverse("cardapi:reward-goal-match"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        goal_result = response.data["cards"][0]["goal_results"][0]
        self.assertEqual(goal_result["status"], "needs_information")
        self.assertEqual(
            goal_result["missing_inputs"],
            [f"account_opened_dates.{self.transfer_card.local_slug}"],
        )
        self.assertEqual(
            response.data["portfolio"]["unresolved_goals"][0]["label"],
            "Fly with Goal API Airline",
        )

    def test_goal_matching_validates_references_and_dates(self):
        self.client.force_authenticate(self.user)
        invalid_program = deepcopy(self.payload)
        invalid_program["goals"][0]["program_codes"] = ["missing-program"]
        unknown_date_card = deepcopy(self.payload)
        unknown_date_card["account_opened_dates"] = {
            "not-in-request": "2026-01-01"
        }
        future_date = deepcopy(self.payload)
        future_date["account_opened_dates"] = {
            self.transfer_card.local_slug: "2026-09-04"
        }

        for invalid_payload in (invalid_program, unknown_date_card, future_date):
            response = self.client.post(
                reverse("cardapi:reward-goal-match"),
                invalid_payload,
                format="json",
            )
            self.assertEqual(response.status_code, 400)


class PortfolioRecommendationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="recommendation@example.com",
            password="recommendation-password",
        )
        self.issuer = Issuer.objects.create(
            slug="recommendation-bank",
            name="Recommendation Bank",
            country="US",
        )
        self.category = RewardCategory.objects.create(
            slug="recommendation-dining",
            category="Recommendation Dining",
        )
        self.current = self._card(
            "recommendation-current",
            "Recommendation Current",
            rate="1",
            fee="0",
            profile=CreditCard.CreditProfile.FAIR,
        )
        self.premium = self._card(
            "recommendation-premium",
            "Recommendation Premium",
            rate="3",
            fee="95",
            profile=CreditCard.CreditProfile.GOOD,
        )
        self.free = self._card(
            "recommendation-free",
            "Recommendation Free",
            rate="2",
            fee="0",
            profile=CreditCard.CreditProfile.FAIR,
        )
        self.goal_card = self._card(
            "recommendation-goal-card",
            "Recommendation Goal Card",
            rate="1.5",
            fee="0",
            profile=CreditCard.CreditProfile.EXCELLENT,
        )
        self.weak = self._card(
            "recommendation-weak",
            "Recommendation Weak",
            rate="0.5",
            fee="0",
            profile=CreditCard.CreditProfile.FAIR,
        )
        self._card(
            "recommendation-business",
            "Recommendation Business",
            rate="10",
            fee="0",
            card_type=CreditCard.CardType.BUSINESS,
        )
        self._card(
            "recommendation-discontinued",
            "Recommendation Discontinued",
            rate="10",
            fee="0",
            is_discontinued=True,
        )
        self.unknown_fee = self._card(
            "recommendation-unknown-fee",
            "Recommendation Unknown Fee",
            rate="8",
            fee=None,
        )
        self.source_program = RewardProgram.objects.create(
            code="recommendation-points",
            name="Recommendation Points",
            unit=RewardProgram.Unit.POINTS,
            program_type=RewardProgram.ProgramType.ISSUER,
            cash_value_cpp=1,
        )
        self.destination_program = RewardProgram.objects.create(
            code="recommendation-airline",
            name="Recommendation Airline",
            unit=RewardProgram.Unit.MILES,
            program_type=RewardProgram.ProgramType.AIRLINE,
        )
        CardRewardProgram.objects.create(
            credit_card=self.goal_card,
            reward_program=self.source_program,
            can_cash_redeem=True,
            can_transfer_partners=True,
        )
        RewardTransferRoute.objects.create(
            source_key="recommendation-transfer-route",
            source_program=self.source_program,
            destination_program=self.destination_program,
            source_amount=1,
            destination_amount=1,
            source_url="https://example.com/recommendation-transfer",
            verified_at=date(2026, 9, 1),
        )
        self.payload = {
            "current_card_slugs": [self.current.local_slug],
            "spending": [
                {
                    "category_slug": self.category.slug,
                    "annual_amount": "10000.00",
                }
            ],
            "goals": [
                {
                    "label": "Recommendation flight",
                    "program_codes": [self.destination_program.code],
                    "priority": "3.0",
                }
            ],
            "annual_fee_budget": "100.00",
            "recommendation_priority": "ongoing_value",
            "valuation_strategy": "cash",
            "as_of": "2026-09-03",
        }

    def _card(
        self,
        slug,
        name,
        *,
        rate,
        fee,
        profile=CreditCard.CreditProfile.FAIR,
        card_type=CreditCard.CardType.PERSONAL,
        is_discontinued=False,
    ):
        card = CreditCard.objects.create(
            local_slug=slug,
            issuer=self.issuer,
            name=name,
            annual_fee=fee,
            card_type=card_type,
            recommended_credit_profile=profile,
            is_discontinued=is_discontinued,
        )
        CCRewardRate.objects.create(
            credit_card=card,
            category=self.category,
            rate_multiplier=rate,
            rate_type=CCRewardRate.RateType.PERCENT_CASHBACK,
            is_base_rate=True,
            source_key=f"{slug}-base-rate",
        )
        return card

    def test_recommendation_requires_authentication(self):
        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            self.payload,
            format="json",
        )

        self.assertIn(response.status_code, (401, 403))

    def test_recommendation_selects_candidates_and_returns_actions(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            self.payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "recommendation_available")
        recommended = response.data["recommended_action"]
        self.assertEqual(recommended["candidate"]["slug"], self.premium.local_slug)
        self.assertEqual(recommended["incremental_recurring_value"], "105.0000")
        self.assertLessEqual(
            Decimal(recommended["total_annual_fees"]), Decimal("100")
        )
        self.assertEqual(response.data["screening"]["candidate_count"], 5)
        self.assertEqual(response.data["screening"]["evaluated_action_count"], 10)
        self.assertEqual(response.data["screening"]["excluded_unknown_fee"], 2)
        action_types = {item["action_type"] for item in response.data["actions"]}
        self.assertEqual(action_types, {"add", "replace"})
        returned_slugs = {
            item["candidate"]["slug"] for item in response.data["actions"]
        }
        self.assertNotIn("recommendation-business", returned_slugs)
        self.assertNotIn("recommendation-discontinued", returned_slugs)
        self.assertNotIn(self.unknown_fee.local_slug, returned_slugs)

    def test_recommendation_enforces_total_fee_budget(self):
        self.client.force_authenticate(self.user)
        payload = {**self.payload, "annual_fee_budget": "0.00"}

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["recommended_action"]["candidate"]["slug"],
            self.free.local_slug,
        )
        self.assertEqual(response.data["screening"]["excluded_over_budget"], 2)
        self.assertTrue(
            all(item["total_annual_fees"] == "0.00" for item in response.data["actions"])
        )

    def test_goal_priority_can_choose_goal_access_over_higher_cash_value(self):
        self.client.force_authenticate(self.user)
        payload = {
            **self.payload,
            "recommendation_priority": "goals",
            "excluded_card_slugs": [self.premium.local_slug],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        recommended = response.data["recommended_action"]
        self.assertEqual(recommended["candidate"]["slug"], self.goal_card.local_slug)
        self.assertEqual(recommended["incremental_goal_priority"], "3.0000")
        self.assertEqual(
            recommended["goal_summary"]["covered_goals"][0]["label"],
            "Recommendation flight",
        )
        goal_result = recommended["goal_summary"]["card_results"][0][
            "goal_results"
        ][0]
        self.assertEqual(goal_result["status"], "matched")
        self.assertEqual(goal_result["options"][0]["method"], "transfer")

    def test_recommendation_can_keep_the_current_setup(self):
        self.client.force_authenticate(self.user)
        payload = {
            **self.payload,
            "goals": [],
            "excluded_card_slugs": [
                self.premium.local_slug,
                self.free.local_slug,
                self.goal_card.local_slug,
            ],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "keep_current_setup")
        self.assertIsNone(response.data["recommended_action"])

    def test_first_year_priority_only_includes_confirmed_bonus(self):
        bonus = SignupBonus.objects.create(
            credit_card=self.premium,
            offer_text="Earn $100 after spending $500 in three months.",
            bonus_amount=100,
            bonus_unit=RewardProgram.Unit.CASH,
            minimum_spend=500,
            minimum_spend_months=3,
            source_key="recommendation-public-offer",
            source_type=SignupBonus.SourceType.CURATED,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )
        self.client.force_authenticate(self.user)
        payload = {
            **self.payload,
            "recommendation_priority": "first_year_value",
            "signup_bonus_uses": [
                {
                    "card_slug": self.premium.local_slug,
                    "eligibility": "eligible",
                    "can_meet_minimum_spend": True,
                }
            ],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        recommended = response.data["recommended_action"]
        self.assertEqual(recommended["candidate"]["slug"], self.premium.local_slug)
        self.assertEqual(recommended["incremental_first_year_value"], "205.0000")
        self.assertEqual(
            recommended["signup_bonus"]["signup_bonus"]["offer_text"],
            bonus.offer_text,
        )
        self.assertTrue(recommended["signup_bonus"]["is_included"])

    def test_recommendation_applies_credit_profile_and_validates_goal_mode(self):
        self.client.force_authenticate(self.user)
        payload = {
            **self.payload,
            "credit_profile": CreditCard.CreditProfile.GOOD,
            "recommendation_priority": "goals",
            "goals": [],
        }

        invalid = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)

        payload["recommendation_priority"] = "ongoing_value"
        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        returned_slugs = {
            item["candidate"]["slug"] for item in response.data["actions"]
        }
        self.assertNotIn(self.goal_card.local_slug, returned_slugs)

    def test_over_budget_setup_prefers_a_feasible_replacement(self):
        self.current.annual_fee = 95
        self.current.save(update_fields=("annual_fee",))
        current_rate = self.current.reward_rates.get()
        current_rate.rate_multiplier = 5
        current_rate.save(update_fields=("rate_multiplier",))
        self.client.force_authenticate(self.user)
        payload = {
            **self.payload,
            "goals": [],
            "annual_fee_budget": "0.00",
            "excluded_card_slugs": [
                self.premium.local_slug,
                self.goal_card.local_slug,
            ],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "recommendation_available")
        recommended = response.data["recommended_action"]
        self.assertEqual(recommended["action_type"], "replace")
        self.assertEqual(recommended["removed_card"]["slug"], self.current.local_slug)
        self.assertEqual(recommended["candidate"]["slug"], self.free.local_slug)
        self.assertLess(Decimal(recommended["incremental_recurring_value"]), 0)

    def test_recommendation_rejects_duplicate_goals_and_unknown_issuers(self):
        self.client.force_authenticate(self.user)
        duplicate_goals = deepcopy(self.payload)
        duplicate_goals["goals"].append(
            {
                "label": "recommendation FLIGHT",
                "program_codes": [self.destination_program.code],
                "priority": "1",
            }
        )
        unknown_issuer = {**self.payload, "issuer_slugs": ["not-an-issuer"]}

        duplicate_response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            duplicate_goals,
            format="json",
        )
        issuer_response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            unknown_issuer,
            format="json",
        )

        self.assertEqual(duplicate_response.status_code, 400)
        self.assertIn("goals", duplicate_response.data)
        self.assertEqual(issuer_response.status_code, 400)
        self.assertIn("issuer_slugs", issuer_response.data)

    def test_recommendation_bounds_the_evaluated_action_count(self):
        extra_current = [
            CreditCard.objects.create(
                local_slug=f"recommendation-current-{index}",
                issuer=self.issuer,
                name=f"Recommendation Current {index}",
                annual_fee=0,
                card_type=CreditCard.CardType.PERSONAL,
            )
            for index in range(1, 20)
        ]
        for index in range(1, 20):
            CreditCard.objects.create(
                local_slug=f"recommendation-extra-candidate-{index}",
                issuer=self.issuer,
                name=f"Recommendation Extra Candidate {index}",
                annual_fee=0,
                card_type=CreditCard.CardType.PERSONAL,
            )
        self.client.force_authenticate(self.user)
        payload = {
            **self.payload,
            "current_card_slugs": [
                self.current.local_slug,
                *(card.local_slug for card in extra_current),
            ],
        }

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("candidate_pool", response.data)
        self.assertIn("maximum is 500", str(response.data["candidate_pool"]))

    def test_recommendation_is_read_only_and_rejects_get(self):
        self.client.force_authenticate(self.user)
        card_count = CreditCard.objects.count()
        modified_date = self.current.modified_date

        response = self.client.post(
            reverse("cardapi:portfolio-recommend"),
            self.payload,
            format="json",
        )
        method_response = self.client.get(reverse("cardapi:portfolio-recommend"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(method_response.status_code, 405)
        self.assertEqual(CreditCard.objects.count(), card_count)
        self.current.refresh_from_db()
        self.assertEqual(self.current.modified_date, modified_date)
        rendered = str(response.data)
        self.assertNotIn("source_key", rendered)
        self.assertNotIn("cardapi_id", rendered)
