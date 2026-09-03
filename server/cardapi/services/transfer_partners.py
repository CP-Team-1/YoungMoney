import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from cardapi.models import CreditCard, RewardProgram, RewardTransferRoute
from cardapi.services.cardapi import CardAPIDataError, _save_changed
from cardapi.services.reward_programs import import_reward_program_payload


def _date(value, field_name):
    if value in (None, ""):
        return None
    parsed = parse_date(str(value))
    if parsed is None:
        raise CardAPIDataError(f"{field_name} must use YYYY-MM-DD format.")
    return parsed


def _positive_decimal(value, field_name):
    if value is None:
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise CardAPIDataError(f"{field_name} must be a number.") from exc
    if result <= 0:
        raise CardAPIDataError(f"{field_name} must be greater than zero.")
    return result


@transaction.atomic
def import_transfer_partner_payload(payload, *, authoritative=True):
    if not isinstance(payload.get("programs", []), list):
        raise CardAPIDataError("Transfer-partner programs must be a list.")
    raw_routes = payload.get("routes") or []
    catalogs = payload.get("catalogs") or []
    if not isinstance(raw_routes, list) or not isinstance(catalogs, list):
        raise CardAPIDataError("Transfer-partner routes and catalogs must be lists.")
    routes = list(raw_routes)
    for catalog in catalogs:
        if not isinstance(catalog, dict) or not isinstance(catalog.get("partners"), list):
            raise CardAPIDataError("Every transfer catalog requires a partners list.")
        missing_catalog_fields = [
            field
            for field in ("source_program_code", "source_url", "verified_at")
            if not catalog.get(field)
        ]
        if missing_catalog_fields:
            raise CardAPIDataError(
                "Transfer catalog is missing: "
                + ", ".join(missing_catalog_fields)
                + "."
            )
        defaults = {
            key: value
            for key, value in catalog.items()
            if key != "partners"
        }
        for partner in catalog["partners"]:
            row = {**defaults, **partner}
            if not row.get("destination_program_code"):
                raise CardAPIDataError("Every transfer partner requires a program code.")
            if not row.get("source_key"):
                identity = [
                    row.get("source_program_code"),
                    row["destination_program_code"],
                    row.get("eligible_card_slug") or "general",
                    row.get("effective_from") or "any-date",
                    row.get("account_opened_before") or "any-before",
                    row.get("account_opened_on_or_after") or "any-after",
                ]
                row["source_key"] = "-".join(identity)
            routes.append(row)

    program_stats = import_reward_program_payload({"programs": payload.get("programs", [])})
    observed_at = timezone.now()
    seen_by_source = {}
    included_source_codes = {
        row.get("source_program_code")
        for row in (*catalogs, *raw_routes)
        if isinstance(row, dict) and row.get("source_program_code")
    }
    included_sources = list(RewardProgram.objects.filter(
        code__in=included_source_codes
    ))
    found_source_codes = {program.code for program in included_sources}
    missing_source_codes = included_source_codes - found_source_codes
    if missing_source_codes:
        raise CardAPIDataError(
            "Unknown source reward programs: "
            + ", ".join(sorted(missing_source_codes))
            + "."
        )
    for source_program in included_sources:
        seen_by_source[source_program.pk] = set()
    created = 0
    updated = 0

    for row in routes:
        if not isinstance(row, dict):
            raise CardAPIDataError("Every transfer route must be an object.")
        required = ("source_key", "source_program_code", "destination_program_code", "source_url", "verified_at")
        missing = [field for field in required if not row.get(field)]
        if missing:
            raise CardAPIDataError(
                "Transfer route is missing: " + ", ".join(missing) + "."
            )
        try:
            source_program = RewardProgram.objects.get(code=row["source_program_code"])
            destination_program = RewardProgram.objects.get(
                code=row["destination_program_code"]
            )
        except RewardProgram.DoesNotExist as exc:
            raise CardAPIDataError(f"Unknown reward program: {exc}.") from exc
        if source_program == destination_program:
            raise CardAPIDataError("A transfer route must connect different programs.")

        source_amount = _positive_decimal(row.get("source_amount"), "source_amount")
        destination_amount = _positive_decimal(
            row.get("destination_amount"), "destination_amount"
        )
        if (source_amount is None) != (destination_amount is None):
            raise CardAPIDataError(
                "source_amount and destination_amount must be supplied together."
            )

        eligible_card = None
        if row.get("eligible_card_slug"):
            try:
                eligible_card = CreditCard.objects.get(
                    local_slug=row["eligible_card_slug"]
                )
            except CreditCard.DoesNotExist as exc:
                raise CardAPIDataError(
                    f"Unknown eligible card {row['eligible_card_slug']!r}."
                ) from exc
            if not eligible_card.reward_program_memberships.filter(
                reward_program=source_program, is_active=True
            ).exists():
                raise CardAPIDataError(
                    f"{eligible_card.name} is not linked to {source_program.name}."
                )

        values = {
            "source_program": source_program,
            "destination_program": destination_program,
            "eligible_card": eligible_card,
            "source_amount": source_amount,
            "destination_amount": destination_amount,
            "minimum_transfer": row.get("minimum_transfer"),
            "transfer_increment": row.get("transfer_increment"),
            "effective_from": _date(row.get("effective_from"), "effective_from"),
            "effective_through": _date(
                row.get("effective_through"), "effective_through"
            ),
            "account_opened_before": _date(
                row.get("account_opened_before"), "account_opened_before"
            ),
            "account_opened_on_or_after": _date(
                row.get("account_opened_on_or_after"),
                "account_opened_on_or_after",
            ),
            "notes": row.get("notes"),
            "source_url": row["source_url"],
            "verified_at": _date(row["verified_at"], "verified_at"),
            "is_active": row.get("is_active", True),
            "last_seen_at": observed_at,
        }
        if (
            values["effective_from"]
            and values["effective_through"]
            and values["effective_from"] > values["effective_through"]
        ):
            raise CardAPIDataError("effective_from cannot follow effective_through.")
        if (
            values["account_opened_before"]
            and values["account_opened_on_or_after"]
            and values["account_opened_on_or_after"]
            >= values["account_opened_before"]
        ):
            raise CardAPIDataError("The account-opening date range is empty.")

        route, was_created = RewardTransferRoute.objects.get_or_create(
            source_key=row["source_key"], defaults=values
        )
        if was_created:
            created += 1
        else:
            _save_changed(route, values)
            updated += 1
        seen_by_source.setdefault(source_program.pk, set()).add(route.source_key)

    if authoritative:
        for source_id, seen_keys in seen_by_source.items():
            RewardTransferRoute.objects.filter(
                source_program_id=source_id
            ).exclude(source_key__in=seen_keys).update(is_active=False)

    return {
        "programs": program_stats["programs"],
        "routes_created": created,
        "routes_updated": updated,
    }


def load_transfer_partner_file(path, *, authoritative=True):
    try:
        with Path(path).open(encoding="utf-8") as source:
            return import_transfer_partner_payload(
                json.load(source), authoritative=authoritative
            )
    except (OSError, json.JSONDecodeError, KeyError, ValidationError) as exc:
        raise CardAPIDataError(f"Could not import transfer partners: {exc}") from exc
