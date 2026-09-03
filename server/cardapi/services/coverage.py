from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from cardapi.models import CreditCard


PRESENT = "present"
MISSING = "missing"
INCOMPLETE = "incomplete"
STALE = "stale"
UNAVAILABLE = "unavailable_on_plan"

FEATURE_FIELDS = {
    "perks": "perks",
    "statement_credits": "statement_credits",
}

CORE_FIELDS = (
    "issuer",
    "card_type",
    "annual_fee",
    "reward_rates",
    "base_reward_rate",
    "reward_program_mapping",
)


def _value_status(value):
    return PRESENT if value is not None and value != "" else MISSING


def _relation_status(count, unavailable):
    if unavailable:
        return UNAVAILABLE
    return PRESENT if count else MISSING


def _is_before(value, cutoff):
    if value is None:
        return False
    if hasattr(value, "date"):
        value = value.date()
    return value < cutoff


def _curated_field_is_stale(card, field, cutoff):
    metadata = (card.curated_sources or {}).get(field) or {}
    checked_on = metadata.get("checked_on")
    if not checked_on:
        return False
    try:
        return date.fromisoformat(checked_on) < cutoff
    except (TypeError, ValueError):
        return True


def _card_report(card, unavailable_features, stale_cutoff):
    needs_reward_program = bool(
        card.active_point_rate_count or card.active_non_cash_bonus_count
    )
    if needs_reward_program and not card.active_primary_program_count:
        program_mapping_status = MISSING
    elif card.unmapped_non_cash_bonus_count:
        program_mapping_status = INCOMPLETE
    else:
        program_mapping_status = PRESENT
    if card.active_transfer_membership_count and not card.active_transfer_route_count:
        transfer_mapping_status = MISSING
    else:
        transfer_mapping_status = PRESENT

    statuses = {
        "cardapi_id": _value_status(card.cardapi_id),
        "issuer": PRESENT,
        "network": _value_status(card.network),
        "card_type": _value_status(card.card_type),
        "annual_fee": _value_status(card.annual_fee),
        "foreign_transaction_fee": _value_status(card.foreign_transaction_fee),
        "credit_score_min": _value_status(card.credit_score_min),
        "reward_currency": _value_status(card.reward_currency),
        "reward_currency_name": _value_status(card.reward_currency_name),
        "application_rules": _value_status(card.application_rules),
        "reward_program_mapping": program_mapping_status,
        "transfer_partner_mapping": transfer_mapping_status,
        "reward_rates": PRESENT if card.active_reward_rate_count else MISSING,
        "base_reward_rate": PRESENT if card.active_base_rate_count else MISSING,
        "signup_bonus": PRESENT if card.active_signup_bonus_count else MISSING,
        "statement_credits": _relation_status(
            card.active_statement_credit_count,
            "statement_credits" in unavailable_features,
        ),
        "perks": _relation_status(
            card.active_perk_count,
            "perks" in unavailable_features,
        ),
    }

    if card.active_reward_rate_count and not card.active_base_rate_count:
        statuses["base_reward_rate"] = INCOMPLETE

    has_point_rates = card.active_point_rate_count > 0
    if has_point_rates and not card.reward_currency:
        statuses["reward_currency"] = INCOMPLETE
    if has_point_rates and not card.reward_currency_name:
        statuses["reward_currency_name"] = INCOMPLETE

    for field in (
        "annual_fee",
        "foreign_transaction_fee",
        "credit_score_min",
        "reward_currency",
        "reward_currency_name",
        "application_rules",
    ):
        if statuses[field] == PRESENT and _curated_field_is_stale(
            card, field, stale_cutoff
        ):
            statuses[field] = STALE

    card_is_stale = _is_before(card.last_synced_at, stale_cutoff)
    recommendation_ready = all(statuses[field] == PRESENT for field in CORE_FIELDS)

    return {
        "slug": card.cardapi_slug or card.local_slug,
        "name": card.name,
        "issuer": card.issuer.name,
        "country": card.issuer.country,
        "recommendation_ready": recommendation_ready,
        "card_data_stale": card_is_stale,
        "statuses": statuses,
    }


def build_coverage_report(
    *, country=None, slugs=None, limit=None, stale_after_days=90, unavailable=None
):
    unavailable_features = set(unavailable or ())
    invalid_features = unavailable_features - FEATURE_FIELDS.keys()
    if invalid_features:
        names = ", ".join(sorted(invalid_features))
        raise ValueError(f"Unknown unavailable features: {names}")

    cards = CreditCard.objects.select_related("issuer").annotate(
        active_reward_rate_count=Count(
            "reward_rates",
            filter=Q(reward_rates__is_active=True),
            distinct=True,
        ),
        active_base_rate_count=Count(
            "reward_rates",
            filter=Q(reward_rates__is_active=True, reward_rates__is_base_rate=True),
            distinct=True,
        ),
        active_point_rate_count=Count(
            "reward_rates",
            filter=Q(
                reward_rates__is_active=True,
                reward_rates__rate_type__in=("multiplier", "points_per_dollar"),
            ),
            distinct=True,
        ),
        active_signup_bonus_count=Count(
            "signup_bonuses",
            filter=Q(signup_bonuses__is_active=True),
            distinct=True,
        ),
        active_non_cash_bonus_count=Count(
            "signup_bonuses",
            filter=Q(
                signup_bonuses__is_active=True,
                signup_bonuses__bonus_unit__in=("points", "miles"),
            ),
            distinct=True,
        ),
        unmapped_non_cash_bonus_count=Count(
            "signup_bonuses",
            filter=Q(
                signup_bonuses__is_active=True,
                signup_bonuses__bonus_unit__in=("points", "miles"),
                signup_bonuses__reward_program__isnull=True,
            ),
            distinct=True,
        ),
        active_primary_program_count=Count(
            "reward_program_memberships",
            filter=Q(
                reward_program_memberships__is_active=True,
                reward_program_memberships__is_primary=True,
            ),
            distinct=True,
        ),
        active_transfer_membership_count=Count(
            "reward_program_memberships",
            filter=Q(
                reward_program_memberships__is_active=True,
                reward_program_memberships__can_transfer_partners=True,
            ),
            distinct=True,
        ),
        active_transfer_route_count=Count(
            "reward_program_memberships__reward_program__outgoing_transfer_routes",
            filter=Q(
                reward_program_memberships__is_active=True,
                reward_program_memberships__reward_program__outgoing_transfer_routes__is_active=True,
            ),
            distinct=True,
        ),
        active_statement_credit_count=Count(
            "statement_credits",
            filter=Q(statement_credits__is_active=True),
            distinct=True,
        ),
        active_perk_count=Count(
            "perks",
            filter=Q(perks__is_active=True),
            distinct=True,
        ),
    )
    if country:
        cards = cards.filter(issuer__country=country)
    if slugs:
        cards = cards.filter(cardapi_slug__in=slugs)
    cards = cards.order_by("cardapi_slug")
    if limit is not None:
        cards = cards[:limit]

    stale_cutoff = timezone.now().date() - timedelta(days=stale_after_days)
    card_reports = [
        _card_report(card, unavailable_features, stale_cutoff) for card in cards
    ]

    status_totals = {status: 0 for status in (PRESENT, MISSING, INCOMPLETE, STALE, UNAVAILABLE)}
    for card_report in card_reports:
        for status in card_report["statuses"].values():
            status_totals[status] += 1

    return {
        "summary": {
            "cards": len(card_reports),
            "recommendation_ready": sum(
                card["recommendation_ready"] for card in card_reports
            ),
            "stale_cards": sum(card["card_data_stale"] for card in card_reports),
            "status_totals": status_totals,
            "unavailable_features": sorted(unavailable_features),
            "stale_after_days": stale_after_days,
        },
        "cards": card_reports,
    }
