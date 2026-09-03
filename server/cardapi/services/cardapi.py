import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from cardapi.models import (
    CCRewardRate,
    CreditCard,
    Issuer,
    Perk,
    RewardCategory,
    RewardCategoryAlias,
    RewardProgram,
    SignupBonus,
    StatementCredit,
)


DEFAULT_BASE_URL = "https://adaptable-dream-production-2fce.up.railway.app"


class CardAPIError(Exception):
    """Base exception for CardAPI requests and payload processing."""


class CardAPIConfigurationError(CardAPIError):
    """Raised when required CardAPI configuration is missing."""


class CardAPIRequestError(CardAPIError):
    """Raised when CardAPI cannot return a successful response."""


class CardAPIDataError(CardAPIError):
    """Raised when a response cannot be mapped safely."""


@dataclass
class ImportStats:
    issuers_created: int = 0
    issuers_updated: int = 0
    cards_created: int = 0
    cards_updated: int = 0
    categories_created: int = 0
    reward_rates_created: int = 0
    reward_rates_updated: int = 0
    signup_bonuses_created: int = 0
    signup_bonuses_updated: int = 0

    def to_dict(self):
        return asdict(self)


class CardAPIClient:
    def __init__(self, api_key=None, base_url=None, timeout=15):
        self.api_key = api_key or os.environ.get("CARDAPI_KEY")
        self.base_url = (
            base_url or os.environ.get("CARDAPI_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            raise CardAPIConfigurationError(
                "CARDAPI_KEY must be set before making CardAPI requests."
            )

    def get_cards(self, *, limit=20, offset=0, country=None):
        parameters = {"limit": limit, "offset": offset}
        if country:
            parameters["country"] = country
        return self._get("/v1/cards", parameters)

    def get_card(self, slug):
        return self._get(f"/v1/cards/{slug}")

    def get_card_perks(self, slug):
        return self._get(f"/v1/cards/{slug}/perks")

    def get_card_credits(self, slug):
        return self._get(f"/v1/cards/{slug}/credits")

    def _get(self, path, parameters=None):
        query = f"?{urlencode(parameters)}" if parameters else ""
        request = Request(
            f"{self.base_url}{path}{query}",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            retry_after = exc.headers.get("Retry-After")
            suffix = f" Retry after {retry_after} seconds." if retry_after else ""
            raise CardAPIRequestError(
                f"CardAPI returned HTTP {exc.code}.{suffix}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise CardAPIRequestError(f"CardAPI request failed: {exc}") from exc


def _uuid_or_none(value):
    if not value:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _datetime_or_none(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return parse_datetime(str(value))


def _non_null_values(payload, mapping):
    return {
        model_field: payload[api_field]
        for api_field, model_field in mapping.items()
        if payload.get(api_field) is not None
    }


def _save_changed(instance, values):
    changed_fields = []
    for field, value in values.items():
        if getattr(instance, field) != value:
            setattr(instance, field, value)
            changed_fields.append(field)
    if changed_fields:
        instance.save(update_fields=changed_fields + ["modified_date"])
    return bool(changed_fields)


def _display_category(slug):
    return str(slug).replace("_", " ").replace("-", " ").title()


def _category_for_source_slug(slug, source="cardapi"):
    alias = RewardCategoryAlias.objects.filter(source=source, alias=slug).first()
    if alias:
        return alias.category, False
    category, created = RewardCategory.objects.get_or_create(
        slug=slug,
        defaults={"category": _display_category(slug)},
    )
    RewardCategoryAlias.objects.get_or_create(
        source=source,
        alias=slug,
        defaults={"category": category},
    )
    return category, created


def _bonus_key(card_data):
    identity = {
        "offer_text": card_data.get("signup_bonus"),
        "bonus_amount": card_data.get("signup_bonus_value"),
        "minimum_spend": card_data.get("signup_min_spend"),
        "minimum_spend_months": card_data.get("signup_min_spend_months"),
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _infer_bonus_unit(offer_text):
    normalized = str(offer_text or "").casefold()
    if "mile" in normalized:
        return RewardProgram.Unit.MILES
    if "point" in normalized:
        return RewardProgram.Unit.POINTS
    if "$" in normalized or "cash" in normalized or "statement credit" in normalized:
        return RewardProgram.Unit.CASH
    return None


def _child_key(prefix, data, fields):
    identity = {field: data.get(field) for field in fields}
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{prefix}-{digest}"


def _upsert_issuer(card_data, observed_at, stats):
    issuer_data = card_data.get("issuers") or card_data.get("issuer")
    if not isinstance(issuer_data, dict):
        raise CardAPIDataError(
            f"Card {card_data.get('slug')!r} has no structured issuer object."
        )

    issuer_id = _uuid_or_none(card_data.get("issuer_id") or issuer_data.get("id"))
    slug = issuer_data.get("slug")
    name = issuer_data.get("name")
    if not slug or not name:
        raise CardAPIDataError("An issuer slug and name are required.")

    issuer = Issuer.objects.filter(cardapi_id=issuer_id).first() if issuer_id else None
    if issuer is None:
        issuer = Issuer.objects.filter(slug=slug).first()

    values = _non_null_values(
        issuer_data,
        {
            "slug": "slug",
            "name": "name",
            "country": "country",
            "website": "website",
            "logo_url": "logo_url",
        },
    )
    values.update({"is_active": True, "last_synced_at": observed_at})
    if issuer_id:
        values["cardapi_id"] = issuer_id

    if issuer is None:
        issuer = Issuer.objects.create(**values)
        stats.issuers_created += 1
    else:
        _save_changed(issuer, values)
        stats.issuers_updated += 1
    return issuer


def _upsert_card(card_data, issuer, observed_at, stats):
    slug = card_data.get("slug")
    name = card_data.get("name")
    if not slug or not name:
        raise CardAPIDataError("Each card requires a slug and name.")

    card_id = _uuid_or_none(card_data.get("id"))
    card = CreditCard.objects.filter(cardapi_id=card_id).first() if card_id else None
    if card is None:
        card = CreditCard.objects.filter(cardapi_slug=slug).first()

    api_values = _non_null_values(
        card_data,
        {
            "slug": "cardapi_slug",
            "name": "name",
            "network": "network",
            "card_type": "card_type",
            "product_family": "product_family",
            "annual_fee": "annual_fee",
            "annual_fee_waived_first_year": "annual_fee_waived_first_year",
            "foreign_transaction_fee": "foreign_transaction_fee",
            "credit_score_min": "credit_score_min",
            "reward_currency": "reward_currency",
            "reward_currency_name": "reward_currency_name",
            "application_rules": "application_rules",
            "is_discontinued": "is_discontinued",
        },
    )
    cardapi_updated_at = _datetime_or_none(card_data.get("updated_at"))
    if cardapi_updated_at:
        api_values["cardapi_updated_at"] = cardapi_updated_at

    # A reviewed issuer page is authoritative until CardAPI supplies a newer,
    # dated value. Undated API payloads must not silently erase reviewed data.
    if card is not None:
        curated_sources = dict(card.curated_sources)
        api_updated_date = cardapi_updated_at.date() if cardapi_updated_at else None
        for field in tuple(api_values):
            source = curated_sources.get(field)
            checked_on = parse_date(str((source or {}).get("checked_on") or ""))
            if source and (api_updated_date is None or checked_on >= api_updated_date):
                api_values.pop(field)

    values = dict(api_values)
    values.update({"issuer": issuer, "last_synced_at": observed_at})
    if card_id:
        values["cardapi_id"] = card_id

    if card is None:
        values["local_slug"] = slug
        card = CreditCard.objects.create(**values)
        stats.cards_created += 1
    else:
        curated_sources = dict(card.curated_sources)
        for field in api_values:
            curated_sources.pop(field, None)
        values["curated_sources"] = curated_sources
        _save_changed(card, values)
        stats.cards_updated += 1
    return card


def _upsert_reward_rates(card, card_data, observed_at, stats, authoritative):
    api_updated_at = _datetime_or_none(card_data.get("updated_at"))
    if (
        card.official_page_verified_at
        and (not api_updated_at or card.official_page_verified_at >= api_updated_at.date())
        and card.reward_rates.filter(source_url__isnull=False, is_active=True).exists()
    ):
        return

    if api_updated_at and card.official_page_verified_at:
        card.reward_rates.filter(source_url__isnull=False).update(is_active=False)

    seen_ids = []
    for rate_data in card_data.get("reward_rates") or []:
        rate_id = _uuid_or_none(rate_data.get("id"))
        category_slug = rate_data.get("category_slug")
        if not rate_id or not category_slug or rate_data.get("rate_multiplier") is None:
            raise CardAPIDataError(
                f"Card {card.cardapi_slug!r} contains an incomplete reward rate."
            )

        category, category_created = _category_for_source_slug(category_slug)
        if category_created:
            stats.categories_created += 1
        elif not category.is_active:
            _save_changed(category, {"is_active": True})

        values = _non_null_values(
            rate_data,
            {
                "rate_multiplier": "rate_multiplier",
                "rate_type": "rate_type",
                "cap_amount": "cap_amount",
                "cap_period": "cap_period",
                "fallback_rate": "fallback_rate",
                "is_base_rate": "is_base_rate",
                "is_rotating": "is_rotating",
                "rotating_quarter": "rotating_quarter",
                "rotating_year": "rotating_year",
                "notes": "notes",
                "booking_channel": "booking_channel",
                "booking_portal": "booking_portal",
                "geographic_scope": "geographic_scope",
                "transaction_method": "transaction_method",
                "merchant_scope": "merchant_scope",
                "enrollment_required": "enrollment_required",
                "minimum_transaction": "minimum_transaction",
            },
        )
        values.update(
            {
                "credit_card": card,
                "category": category,
                "cardapi_created_at": _datetime_or_none(rate_data.get("created_at")),
                "is_active": True,
                "last_seen_at": observed_at,
                "valid_from": parse_date(str(rate_data.get("valid_from") or "")),
                "expires_on": parse_date(str(rate_data.get("expires_on") or "")),
            }
        )
        rate, created = CCRewardRate.objects.get_or_create(
            cardapi_id=rate_id,
            defaults=values,
        )
        if created:
            stats.reward_rates_created += 1
        else:
            _save_changed(rate, values)
            stats.reward_rates_updated += 1
        seen_ids.append(rate_id)

    if authoritative:
        CCRewardRate.objects.filter(
            credit_card=card,
            cardapi_id__isnull=False,
        ).exclude(cardapi_id__in=seen_ids).update(is_active=False)


def _upsert_signup_bonus(card, card_data, observed_at, stats, authoritative):
    api_updated_at = _datetime_or_none(card_data.get("updated_at"))
    if (
        card.official_page_verified_at
        and (not api_updated_at or card.official_page_verified_at >= api_updated_at.date())
        and card.signup_bonuses.filter(
            source_type=SignupBonus.SourceType.CURATED,
            is_active=True,
        ).exists()
    ):
        return

    if api_updated_at and card.official_page_verified_at:
        card.signup_bonuses.filter(
            source_type=SignupBonus.SourceType.CURATED
        ).update(is_active=False)

    offer_text = card_data.get("signup_bonus")
    if offer_text:
        source_key = _bonus_key(card_data)
        bonus_unit = _infer_bonus_unit(offer_text)
        membership = (
            card.reward_program_memberships.filter(is_active=True, is_primary=True)
            .select_related("reward_program")
            .first()
        )
        values = {
            "offer_text": offer_text,
            "bonus_amount": card_data.get("signup_bonus_value"),
            "bonus_unit": bonus_unit or (
                membership.reward_program.unit if membership else None
            ),
            "reward_program": (
                membership.reward_program
                if membership and bonus_unit == membership.reward_program.unit
                else None
            ),
            "minimum_spend": card_data.get("signup_min_spend"),
            "minimum_spend_months": card_data.get("signup_min_spend_months"),
            "is_active": True,
            "last_seen_at": observed_at,
        }
        bonus, created = SignupBonus.objects.get_or_create(
            credit_card=card,
            source_type=SignupBonus.SourceType.CARDAPI,
            source_key=source_key,
            defaults={"first_seen_at": observed_at, **values},
        )
        if created:
            stats.signup_bonuses_created += 1
        else:
            _save_changed(bonus, values)
            stats.signup_bonuses_updated += 1

        SignupBonus.objects.filter(
            credit_card=card,
            source_type=SignupBonus.SourceType.CARDAPI,
        ).exclude(pk=bonus.pk).update(is_active=False)
    elif authoritative:
        SignupBonus.objects.filter(
            credit_card=card,
            source_type=SignupBonus.SourceType.CARDAPI,
        ).update(is_active=False)


@transaction.atomic
def import_cards_payload(payload: dict[str, Any], *, authoritative_child_data=False):
    cards = payload.get("data")
    if not isinstance(cards, list):
        raise CardAPIDataError("CardAPI response must contain a data list.")

    observed_at = timezone.now()
    stats = ImportStats()
    for card_data in cards:
        if not isinstance(card_data, dict):
            raise CardAPIDataError("Every card in the response must be an object.")
        issuer = _upsert_issuer(card_data, observed_at, stats)
        card = _upsert_card(card_data, issuer, observed_at, stats)
        _upsert_reward_rates(
            card,
            card_data,
            observed_at,
            stats,
            authoritative_child_data,
        )
        _upsert_signup_bonus(
            card,
            card_data,
            observed_at,
            stats,
            authoritative_child_data,
        )
    return stats


def _card_for_slug(card_slug):
    try:
        return CreditCard.objects.get(cardapi_slug=card_slug)
    except CreditCard.DoesNotExist as exc:
        raise CardAPIDataError(f"Unknown card slug {card_slug!r}.") from exc


@transaction.atomic
def import_statement_credits_payload(card_slug, payload, *, authoritative=True):
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise CardAPIDataError("Statement-credit response must contain a data list.")

    card = _card_for_slug(card_slug)
    observed_at = timezone.now()
    seen_primary_keys = []
    for row in rows:
        if not isinstance(row, dict):
            raise CardAPIDataError("Every statement credit must be an object.")
        name = row.get("credit_name") or row.get("name")
        if not name:
            raise CardAPIDataError("Every statement credit requires a name.")
        cardapi_id = _uuid_or_none(row.get("id"))
        source_key = None
        if not cardapi_id:
            source_key = _child_key(
                "cardapi-credit",
                row,
                ("credit_name", "name", "credit_amount", "amount", "credit_period", "period"),
            )

        values = {
            "credit_card": card,
            "name": name,
            "amount": row.get("credit_amount", row.get("amount")),
            "period": row.get("credit_period", row.get("period")),
            "eligible_merchants": row.get("eligible_merchants"),
            "enrollment_required": row.get("enrollment_required"),
            "notes": row.get("notes", row.get("description")),
            "is_active": True,
            "last_seen_at": observed_at,
            "source_key": source_key,
        }
        if cardapi_id:
            credit, created = StatementCredit.objects.get_or_create(
                cardapi_id=cardapi_id,
                defaults=values,
            )
        else:
            credit, created = StatementCredit.objects.get_or_create(
                credit_card=card,
                source_key=source_key,
                defaults=values,
            )
        if not created:
            _save_changed(credit, values)
        seen_primary_keys.append(credit.pk)

    if authoritative:
        api_rows = StatementCredit.objects.filter(credit_card=card).filter(
            Q(cardapi_id__isnull=False) | Q(source_key__startswith="cardapi-credit-")
        )
        api_rows.exclude(pk__in=seen_primary_keys).update(is_active=False)
    return {"processed": len(seen_primary_keys)}


@transaction.atomic
def import_perks_payload(card_slug, payload, *, authoritative=True):
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise CardAPIDataError("Perk response must contain a data list.")

    card = _card_for_slug(card_slug)
    observed_at = timezone.now()
    seen_primary_keys = []
    for row in rows:
        if not isinstance(row, dict):
            raise CardAPIDataError("Every perk must be an object.")
        name = row.get("perk_name") or row.get("name")
        if not name:
            raise CardAPIDataError("Every perk requires a name.")
        cardapi_id = _uuid_or_none(row.get("id"))
        source_key = None
        if not cardapi_id:
            source_key = _child_key(
                "cardapi-perk",
                row,
                ("perk_name", "name", "perk_type", "category", "perk_period", "frequency"),
            )

        values = {
            "credit_card": card,
            "perk_type": row.get("perk_type", row.get("category")),
            "name": name,
            "value": row.get("perk_value", row.get("value")),
            "period": row.get("perk_period", row.get("frequency")),
            "partner": row.get("partner"),
            "details": row.get("details", row.get("description")),
            "enrollment_required": row.get("enrollment_required"),
            "spend_requirement": row.get("spend_requirement"),
            "expires_on": parse_date(str(row.get("expires_on") or "")),
            "geographic_scope": row.get("geographic_scope"),
            "is_complimentary": row.get("is_complimentary"),
            "coverage_type": row.get("coverage_type"),
            "benefit_limit": row.get("benefit_limit"),
            "recommendation_notes": row.get("recommendation_notes"),
            "is_active": True,
            "last_seen_at": observed_at,
            "source_key": source_key,
        }
        if cardapi_id:
            perk, created = Perk.objects.get_or_create(
                cardapi_id=cardapi_id,
                defaults=values,
            )
        else:
            perk, created = Perk.objects.get_or_create(
                credit_card=card,
                source_key=source_key,
                defaults=values,
            )
        if not created:
            _save_changed(perk, values)
        seen_primary_keys.append(perk.pk)

    if authoritative:
        api_rows = Perk.objects.filter(credit_card=card).filter(
            Q(cardapi_id__isnull=False) | Q(source_key__startswith="cardapi-perk-")
        )
        api_rows.exclude(pk__in=seen_primary_keys).update(is_active=False)
    return {"processed": len(seen_primary_keys)}


CURATABLE_CARD_FIELDS = {
    "network",
    "card_type",
    "product_family",
    "recommended_credit_profile",
    "annual_fee",
    "annual_fee_waived_first_year",
    "foreign_transaction_fee",
    "credit_score_min",
    "reward_currency",
    "reward_currency_name",
    "application_rules",
    "is_discontinued",
}


def _provenance_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _curated_metadata(item):
    source_url = item.get("source_url")
    verified_at = parse_date(str(item.get("verified_at") or ""))
    if not source_url or not verified_at:
        raise CardAPIDataError(
            "Every curated record requires source_url and verified_at (YYYY-MM-DD)."
        )
    return source_url, verified_at


@transaction.atomic
def import_curated_payload(payload: dict[str, Any]):
    """Fill CardAPI gaps from a reviewed, version-controlled JSON payload."""
    items = payload.get("data")
    if not isinstance(items, list):
        raise CardAPIDataError("Curated payload must contain a data list.")

    stats = {
        "cards_created": 0,
        "cards_updated": 0,
        "reward_rates_created": 0,
        "reward_rates_updated": 0,
        "signup_bonuses_created": 0,
        "signup_bonuses_updated": 0,
        "statement_credits_created": 0,
        "statement_credits_updated": 0,
        "perks_created": 0,
        "perks_updated": 0,
    }
    now = timezone.now()

    for item in items:
        if not isinstance(item, dict):
            raise CardAPIDataError("Every curated card entry must be an object.")
        cardapi_slug = item.get("cardapi_slug")
        local_slug = item.get("local_slug") or cardapi_slug
        card = None
        if cardapi_slug:
            card = CreditCard.objects.filter(cardapi_slug=cardapi_slug).first()
        if card is None and local_slug:
            card = CreditCard.objects.filter(local_slug=local_slug).first()
        if card is None:
            name = item.get("name")
            issuer_slug = item.get("issuer_slug")
            if not local_slug or not name or not issuer_slug:
                raise CardAPIDataError(
                    "An official-only card requires local_slug, name, and issuer_slug."
                )
            try:
                issuer = Issuer.objects.get(slug=issuer_slug)
            except Issuer.DoesNotExist as exc:
                raise CardAPIDataError(
                    f"Curated data references unknown issuer {issuer_slug!r}."
                ) from exc
            card = CreditCard.objects.create(
                local_slug=local_slug,
                cardapi_slug=cardapi_slug,
                issuer=issuer,
                name=name,
            )
            stats["cards_created"] += 1

        source_url, verified_at = _curated_metadata(item)
        source_updated_at = parse_date(str(item.get("source_updated_at") or ""))
        requested_fields = item.get("fields") or {}
        unknown_fields = set(requested_fields) - CURATABLE_CARD_FIELDS
        if unknown_fields:
            names = ", ".join(sorted(unknown_fields))
            raise CardAPIDataError(f"Unsupported curated card fields: {names}.")

        sources = dict(card.curated_sources)
        card_values = {
            "product_url": source_url,
            "official_page_verified_at": verified_at,
        }
        if source_updated_at:
            card_values["official_page_updated_at"] = source_updated_at
        for field, value in requested_fields.items():
            if value is None:
                continue
            previous = getattr(card, field)
            previous_source = sources.get(field)
            card_values[field] = value
            metadata = {
                "url": source_url,
                "checked_on": verified_at.isoformat(),
                "source_type": "official_issuer",
            }
            if previous != value:
                metadata["previous_value"] = _provenance_value(previous)
                metadata["previous_source"] = (
                    "official_issuer" if previous_source else "cardapi"
                )
            sources[field] = metadata
        if card_values:
            card_values["curated_sources"] = sources
            _save_changed(card, card_values)
            stats["cards_updated"] += 1

        curated_rate_ids = []
        for rate_data in item.get("reward_rates") or []:
            rate_source_url, rate_verified_at = _curated_metadata(
                {**item, **rate_data}
            )
            source_key = rate_data.get("source_key")
            category_slug = rate_data.get("category_slug")
            if not source_key or not category_slug:
                raise CardAPIDataError(
                    "Curated reward rates require source_key and category_slug."
                )
            if rate_data.get("rate_multiplier") is None or not rate_data.get(
                "rate_type"
            ):
                raise CardAPIDataError(
                    "Curated reward rates require rate_multiplier and rate_type."
                )

            category, _ = _category_for_source_slug(category_slug, source="curated")
            values = _non_null_values(
                rate_data,
                {
                    "rate_multiplier": "rate_multiplier",
                    "rate_type": "rate_type",
                    "cap_amount": "cap_amount",
                    "cap_period": "cap_period",
                    "fallback_rate": "fallback_rate",
                    "is_base_rate": "is_base_rate",
                    "is_rotating": "is_rotating",
                    "rotating_quarter": "rotating_quarter",
                    "rotating_year": "rotating_year",
                    "notes": "notes",
                    "booking_channel": "booking_channel",
                    "booking_portal": "booking_portal",
                    "geographic_scope": "geographic_scope",
                    "transaction_method": "transaction_method",
                    "merchant_scope": "merchant_scope",
                    "enrollment_required": "enrollment_required",
                    "minimum_transaction": "minimum_transaction",
                },
            )
            values.update(
                {
                    "category": category,
                    "is_active": True,
                    "last_seen_at": now,
                    "source_url": rate_source_url,
                    "verified_at": rate_verified_at,
                    "valid_from": parse_date(str(rate_data.get("valid_from") or "")),
                    "expires_on": parse_date(str(rate_data.get("expires_on") or "")),
                }
            )
            rate, created = CCRewardRate.objects.get_or_create(
                credit_card=card,
                source_key=source_key,
                defaults=values,
            )
            if not created:
                _save_changed(rate, values)
            curated_rate_ids.append(rate.pk)
            key = "reward_rates_created" if created else "reward_rates_updated"
            stats[key] += 1

        if "reward_rates" in item:
            card.reward_rates.exclude(pk__in=curated_rate_ids).update(is_active=False)

        curated_bonus_ids = []
        for bonus_data in item.get("signup_bonuses") or []:
            bonus_source_url, bonus_verified_at = _curated_metadata(
                {**item, **bonus_data}
            )
            source_key = bonus_data.get("source_key")
            offer_text = bonus_data.get("offer_text")
            if not source_key or not offer_text:
                raise CardAPIDataError(
                    "Curated signup bonuses require source_key and offer_text."
                )
            reward_program = None
            reward_program_code = bonus_data.get("reward_program_code")
            if reward_program_code:
                try:
                    reward_program = RewardProgram.objects.get(
                        code=reward_program_code
                    )
                except RewardProgram.DoesNotExist as exc:
                    raise CardAPIDataError(
                        f"Unknown reward program {reward_program_code!r}."
                    ) from exc
            else:
                membership = (
                    card.reward_program_memberships.filter(
                        is_active=True, is_primary=True
                    )
                    .select_related("reward_program")
                    .first()
                )
                reward_program = membership.reward_program if membership else None
            values = {
                "offer_text": offer_text,
                "bonus_amount": bonus_data.get(
                    "bonus_amount", bonus_data.get("reported_value")
                ),
                "bonus_unit": bonus_data.get("bonus_unit") or (
                    reward_program.unit
                    if reward_program
                    else _infer_bonus_unit(offer_text)
                ),
                "reward_program": reward_program,
                "minimum_spend": bonus_data.get("minimum_spend"),
                "minimum_spend_months": bonus_data.get("minimum_spend_months"),
                "source_url": bonus_source_url,
                "verified_at": bonus_verified_at,
                "is_active": bonus_data.get("is_active", True),
                "last_seen_at": now,
            }
            bonus, created = SignupBonus.objects.get_or_create(
                credit_card=card,
                source_type=SignupBonus.SourceType.CURATED,
                source_key=source_key,
                defaults={"first_seen_at": now, **values},
            )
            if not created:
                _save_changed(bonus, values)
            curated_bonus_ids.append(bonus.pk)
            key = "signup_bonuses_created" if created else "signup_bonuses_updated"
            stats[key] += 1

        if "signup_bonuses" in item:
            card.signup_bonuses.exclude(pk__in=curated_bonus_ids).update(
                is_active=False
            )

        curated_credit_ids = []
        for credit_data in item.get("statement_credits") or []:
            credit_source_url, credit_verified_at = _curated_metadata(
                {**item, **credit_data}
            )
            source_key = credit_data.get("source_key")
            name = credit_data.get("name")
            if not source_key or not name:
                raise CardAPIDataError(
                    "Curated statement credits require source_key and name."
                )
            values = {
                "name": name,
                "amount": credit_data.get("amount"),
                "period": credit_data.get("period"),
                "eligible_merchants": credit_data.get("eligible_merchants"),
                "enrollment_required": credit_data.get("enrollment_required"),
                "notes": credit_data.get("notes"),
                "source_url": credit_source_url,
                "verified_at": credit_verified_at,
                "is_active": credit_data.get("is_active", True),
                "last_seen_at": now,
            }
            credit, created = StatementCredit.objects.get_or_create(
                credit_card=card,
                source_key=source_key,
                defaults=values,
            )
            if not created:
                _save_changed(credit, values)
            curated_credit_ids.append(credit.pk)
            key = "statement_credits_created" if created else "statement_credits_updated"
            stats[key] += 1

        if "statement_credits" in item:
            card.statement_credits.exclude(pk__in=curated_credit_ids).update(
                is_active=False
            )

        curated_perk_ids = []
        for perk_data in item.get("perks") or []:
            perk_source_url, perk_verified_at = _curated_metadata(
                {**item, **perk_data}
            )
            source_key = perk_data.get("source_key")
            name = perk_data.get("name")
            if not source_key or not name:
                raise CardAPIDataError("Curated perks require source_key and name.")
            values = {
                "perk_type": perk_data.get("perk_type"),
                "name": name,
                "value": perk_data.get("value"),
                "period": perk_data.get("period"),
                "partner": perk_data.get("partner"),
                "details": perk_data.get("details"),
                "enrollment_required": perk_data.get("enrollment_required"),
                "spend_requirement": perk_data.get("spend_requirement"),
                "expires_on": parse_date(str(perk_data.get("expires_on") or "")),
                "geographic_scope": perk_data.get("geographic_scope"),
                "is_complimentary": perk_data.get("is_complimentary"),
                "coverage_type": perk_data.get("coverage_type"),
                "benefit_limit": perk_data.get("benefit_limit"),
                "recommendation_notes": perk_data.get("recommendation_notes"),
                "source_url": perk_source_url,
                "verified_at": perk_verified_at,
                "is_active": perk_data.get("is_active", True),
                "last_seen_at": now,
            }
            perk, created = Perk.objects.get_or_create(
                credit_card=card,
                source_key=source_key,
                defaults=values,
            )
            if not created:
                _save_changed(perk, values)
            curated_perk_ids.append(perk.pk)
            key = "perks_created" if created else "perks_updated"
            stats[key] += 1

        if "perks" in item:
            card.perks.exclude(pk__in=curated_perk_ids).update(is_active=False)

    return stats
