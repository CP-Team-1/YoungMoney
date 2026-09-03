from dataclasses import dataclass, replace
from decimal import Decimal

from cardapi.models import CreditCard, RewardProgramUnlock
from cardapi.services.rewards import RewardMatchResult, match_reward_rate


@dataclass(frozen=True)
class CardComparisonResult:
    card: CreditCard
    match: RewardMatchResult
    reward_program_code: str | None
    valuation_strategy: str
    cents_per_point: Decimal | None
    estimated_value: Decimal | None
    effective_return_percent: Decimal | None
    unlocked_by: CreditCard | None
    rank: int | None = None


def _valuation(membership, strategy, custom_cpp):
    program = membership.reward_program
    if strategy == "cash":
        return program.cash_value_cpp if membership.can_cash_redeem else None
    if strategy == "travel_portal":
        return program.travel_portal_cpp if membership.can_use_travel_portal else None
    if strategy == "transfer":
        if not membership.can_transfer_partners:
            return None
        override = (custom_cpp or {}).get(program.code)
        return Decimal(str(override)) if override is not None else program.transfer_value_cpp
    if strategy == "user":
        value = (custom_cpp or {}).get(program.code)
        return Decimal(str(value)) if value is not None else None
    raise ValueError("valuation_strategy must be cash, travel_portal, transfer, or user.")


def _portfolio_unlock(card, membership, strategy, owned_card_ids):
    capability = {
        "transfer": RewardProgramUnlock.Capability.TRANSFER_PARTNERS,
        "travel_portal": RewardProgramUnlock.Capability.TRAVEL_PORTAL,
    }.get(strategy)
    if not capability:
        return None
    return (
        RewardProgramUnlock.objects.filter(
            reward_program=membership.reward_program,
            source_card=card,
            required_card_id__in=owned_card_ids,
            capability=capability,
            is_active=True,
        )
        .select_related("required_card")
        .first()
    )


def value_reward_match(
    *,
    card,
    match,
    owned_cards=(),
    valuation_strategy="cash",
    custom_cpp=None,
    reward_program=None,
):
    """Convert one matched reward result into a defensible dollar value."""
    owned_card_ids = {owned_card.pk for owned_card in owned_cards}
    memberships = card.reward_program_memberships.filter(is_active=True)
    if reward_program is None:
        memberships = memberships.filter(is_primary=True)
    else:
        memberships = memberships.filter(reward_program=reward_program)
    membership = memberships.select_related("reward_program").first()
    program_code = membership.reward_program.code if membership else None
    cpp = None
    estimated_value = None
    effective_return = None
    unlocked_by = None

    if match.status == "matched" and match.reward_amount is not None:
        if match.reward_unit == "cash":
            estimated_value = match.reward_amount
        elif membership:
            cpp = _valuation(membership, valuation_strategy, custom_cpp)
            unlock = _portfolio_unlock(
                card, membership, valuation_strategy, owned_card_ids
            )
            if unlock:
                unlocked_by = unlock.required_card
                if valuation_strategy == "transfer":
                    override = (custom_cpp or {}).get(program_code)
                    cpp = (
                        Decimal(str(override))
                        if override is not None
                        else membership.reward_program.transfer_value_cpp
                    )
                elif valuation_strategy == "travel_portal":
                    cpp = membership.reward_program.travel_portal_cpp
            if cpp is not None:
                estimated_value = match.reward_amount * cpp / Decimal("100")

    return CardComparisonResult(
        card=card,
        match=match,
        reward_program_code=program_code,
        valuation_strategy=valuation_strategy,
        cents_per_point=cpp,
        estimated_value=estimated_value,
        effective_return_percent=effective_return,
        unlocked_by=unlocked_by,
    )


def compare_cards(
    *,
    cards,
    category,
    amount,
    owned_cards=(),
    valuation_strategy="cash",
    custom_cpp=None,
    **purchase_context,
):
    """Match one purchase against cards and rank defensible dollar estimates."""
    cards = list(cards)
    purchase_amount = Decimal(str(amount))
    results = []

    for card in cards:
        match = match_reward_rate(
            card=card,
            category=category,
            amount=purchase_amount,
            **purchase_context,
        )
        result = value_reward_match(
            card=card,
            match=match,
            owned_cards=owned_cards,
            valuation_strategy=valuation_strategy,
            custom_cpp=custom_cpp,
        )
        if result.estimated_value is not None and purchase_amount:
            result = replace(
                result,
                effective_return_percent=(
                    result.estimated_value / purchase_amount * Decimal("100")
                ),
            )
        results.append(result)

    ranked = sorted(
        results,
        key=lambda result: (
            result.estimated_value is not None,
            result.estimated_value or Decimal("-1"),
        ),
        reverse=True,
    )
    rank = 0
    final = []
    for result in ranked:
        if result.estimated_value is not None:
            rank += 1
            result = replace(result, rank=rank)
        final.append(result)
    return final
