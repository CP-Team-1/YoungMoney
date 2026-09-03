import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.dateparse import parse_date

from cardapi.models import (
    CardRewardProgram,
    CreditCard,
    Issuer,
    RewardProgram,
    RewardProgramUnlock,
)
from cardapi.services.cardapi import CardAPIDataError, _save_changed


def _verified_date(row):
    verified_at = parse_date(str(row.get("verified_at") or ""))
    if not row.get("source_url") or not verified_at:
        raise CardAPIDataError("Every rewards record requires source_url and verified_at.")
    return verified_at


@transaction.atomic
def import_reward_program_payload(payload):
    stats = {"programs": 0, "memberships": 0, "unlocks": 0}
    for row in payload.get("programs") or []:
        verified_at = _verified_date(row)
        issuer = None
        if row.get("issuer_slug"):
            issuer = Issuer.objects.get(slug=row["issuer_slug"])
        values = {
            "name": row["name"], "issuer": issuer, "unit": row["unit"],
            "program_type": row.get("program_type") or (
                RewardProgram.ProgramType.CASH
                if row["unit"] == RewardProgram.Unit.CASH
                else RewardProgram.ProgramType.ISSUER
            ),
            "cash_value_cpp": row.get("cash_value_cpp"),
            "travel_portal_cpp": row.get("travel_portal_cpp"),
            "transfer_value_cpp": row.get("transfer_value_cpp"),
            "source_url": row["source_url"], "verified_at": verified_at,
            "is_active": row.get("is_active", True),
        }
        program, created = RewardProgram.objects.get_or_create(code=row["code"], defaults=values)
        if not created:
            _save_changed(program, values)
        stats["programs"] += 1

    for row in payload.get("memberships") or []:
        verified_at = _verified_date(row)
        card = CreditCard.objects.get(local_slug=row["card_slug"])
        program = RewardProgram.objects.get(code=row["program_code"])
        values = {
            "is_primary": row.get("is_primary", True),
            "can_cash_redeem": row.get("can_cash_redeem", False),
            "can_use_travel_portal": row.get("can_use_travel_portal", False),
            "can_transfer_partners": row.get("can_transfer_partners", False),
            "can_combine_rewards": row.get("can_combine_rewards", False),
            "source_url": row["source_url"], "verified_at": verified_at,
            "is_active": row.get("is_active", True),
        }
        membership, created = CardRewardProgram.objects.get_or_create(
            credit_card=card, reward_program=program, defaults=values
        )
        if not created:
            _save_changed(membership, values)
        card.signup_bonuses.filter(
            reward_program__isnull=True,
            bonus_unit=program.unit,
        ).update(reward_program=program)
        stats["memberships"] += 1

    for row in payload.get("unlocks") or []:
        verified_at = _verified_date(row)
        program = RewardProgram.objects.get(code=row["program_code"])
        source_card = CreditCard.objects.get(local_slug=row["source_card_slug"])
        required_card = CreditCard.objects.get(local_slug=row["required_card_slug"])
        values = {
            "conversion_ratio": row.get("conversion_ratio", 1),
            "source_url": row["source_url"], "verified_at": verified_at,
            "is_active": row.get("is_active", True),
        }
        unlock, created = RewardProgramUnlock.objects.get_or_create(
            reward_program=program, source_card=source_card,
            required_card=required_card, capability=row["capability"],
            defaults=values,
        )
        if not created:
            _save_changed(unlock, values)
        stats["unlocks"] += 1
    return stats


def load_reward_program_file(path):
    try:
        with Path(path).open(encoding="utf-8") as source:
            return import_reward_program_payload(json.load(source))
    except (OSError, json.JSONDecodeError, KeyError, ValidationError) as exc:
        raise CardAPIDataError(f"Could not import reward programs: {exc}") from exc
