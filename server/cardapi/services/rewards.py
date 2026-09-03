from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q

from cardapi.models import CCRewardRate, CreditCard, RewardCategory


class RewardMatchError(ValueError):
    """Raised when a purchase cannot be evaluated safely."""


@dataclass(frozen=True)
class RewardMatchResult:
    status: str
    reward_rate: CCRewardRate | None
    reward_amount: Decimal | None
    reward_unit: str | None
    matched_amount: Decimal | None
    fallback_amount: Decimal | None
    explanation: tuple[str, ...]
    warnings: tuple[str, ...]
    missing_inputs: tuple[str, ...] = ()


def _decimal(value, field_name):
    try:
        result = Decimal(str(value))
    except (TypeError, ValueError, ArithmeticError) as exc:
        raise RewardMatchError(f"{field_name} must be a number.") from exc
    if result < 0:
        raise RewardMatchError(f"{field_name} cannot be negative.")
    return result


def _category_lineage(category):
    lineage = []
    current = category
    while current is not None:
        if current in lineage:
            raise RewardMatchError("Reward category hierarchy contains a cycle.")
        lineage.append(current)
        current = current.parent
    return lineage


def _normalize(value):
    return str(value).strip().casefold() if value is not None else None


def _qualifier_state(rate, context):
    missing = []
    checks = (
        ("booking_channel", rate.booking_channel),
        ("booking_portal", rate.booking_portal),
        ("transaction_method", rate.transaction_method),
    )
    for name, required in checks:
        if not required:
            continue
        supplied = context.get(name)
        if supplied is None:
            missing.append(name)
        elif _normalize(supplied) != _normalize(required):
            return False, ()

    if rate.geographic_scope and _normalize(rate.geographic_scope) != "worldwide":
        supplied = context.get("geographic_scope")
        if supplied is None:
            missing.append("geographic_scope")
        elif _normalize(supplied) != _normalize(rate.geographic_scope):
            return False, ()

    if rate.merchant_scope:
        eligible = context.get("merchant_eligible")
        if eligible is None:
            missing.append("merchant_eligible")
        elif not eligible:
            return False, ()

    if rate.enrollment_required:
        enrolled = context.get("enrolled")
        if enrolled is None:
            missing.append("enrolled")
        elif not enrolled:
            return False, ()

    return True, tuple(missing)


def _specificity(rate, distance):
    qualifier_count = sum(
        bool(value)
        for value in (
            rate.booking_channel,
            rate.booking_portal,
            rate.geographic_scope,
            rate.transaction_method,
            rate.merchant_scope,
            rate.enrollment_required,
            rate.minimum_transaction,
        )
    )
    category_score = 0 if rate.is_base_rate else max(1, 50 - distance * 5)
    return qualifier_count * 100 + category_score


def _reward_for(amount, rate_value, rate_type):
    if rate_type == CCRewardRate.RateType.PERCENT_CASHBACK:
        return amount * rate_value / Decimal("100"), "cash"
    return amount * rate_value, "points"


def match_reward_rate(
    *,
    card: CreditCard,
    category: RewardCategory | str,
    amount,
    purchase_date=None,
    booking_channel=None,
    booking_portal=None,
    geographic_scope=None,
    transaction_method=None,
    merchant_eligible=None,
    enrolled=None,
    category_spend_to_date=None,
):
    """Select and calculate the single reward rule for one purchase."""
    amount = _decimal(amount, "amount")
    purchase_date = purchase_date or date.today()
    if isinstance(category, str):
        try:
            category = RewardCategory.objects.get(slug=category)
        except RewardCategory.DoesNotExist as exc:
            raise RewardMatchError(f"Unknown reward category {category!r}.") from exc

    lineage = _category_lineage(category)
    distances = {item.pk: index for index, item in enumerate(lineage)}
    candidates = list(
        card.reward_rates.filter(is_active=True)
        .filter(Q(category__in=lineage) | Q(is_base_rate=True))
        .filter(Q(valid_from__isnull=True) | Q(valid_from__lte=purchase_date))
        .filter(Q(expires_on__isnull=True) | Q(expires_on__gte=purchase_date))
        .select_related("category")
    )

    context = {
        "booking_channel": booking_channel,
        "booking_portal": booking_portal,
        "geographic_scope": geographic_scope,
        "transaction_method": transaction_method,
        "merchant_eligible": merchant_eligible,
        "enrolled": enrolled,
    }
    applicable = []
    unresolved = []
    for rate in candidates:
        if rate.minimum_transaction is not None and amount < rate.minimum_transaction:
            continue
        compatible, missing = _qualifier_state(rate, context)
        if not compatible:
            continue
        distance = distances.get(rate.category_id, len(lineage) + 1)
        score = _specificity(rate, distance)
        if missing:
            unresolved.append((rate, score, missing))
        else:
            applicable.append((rate, score))

    applicable.sort(key=lambda item: (item[1], item[0].rate_multiplier), reverse=True)
    best = applicable[0] if applicable else None
    consequential = [item for item in unresolved if best is None or item[1] >= best[1]]
    if consequential:
        missing = sorted({name for _, _, fields in consequential for name in fields})
        return RewardMatchResult(
            status="needs_information",
            reward_rate=None,
            reward_amount=None,
            reward_unit=None,
            matched_amount=None,
            fallback_amount=None,
            explanation=("A more specific reward rule may apply to this purchase.",),
            warnings=(),
            missing_inputs=tuple(missing),
        )

    if best is None:
        return RewardMatchResult(
            status="no_match",
            reward_rate=None,
            reward_amount=None,
            reward_unit=None,
            matched_amount=None,
            fallback_amount=None,
            explanation=("No active reward rule matches this purchase.",),
            warnings=(),
        )

    rate = best[0]
    matched_amount = amount
    fallback_amount = Decimal("0")
    warnings = []
    if rate.cap_amount is not None:
        if category_spend_to_date is None:
            return RewardMatchResult(
                status="needs_information",
                reward_rate=rate,
                reward_amount=None,
                reward_unit=None,
                matched_amount=None,
                fallback_amount=None,
                explanation=(f"Matched {rate.category.category} at {rate.rate_multiplier}.",),
                warnings=(f"This rate has a {rate.cap_period or 'periodic'} spending cap.",),
                missing_inputs=("category_spend_to_date",),
            )
        spent = _decimal(category_spend_to_date, "category_spend_to_date")
        remaining = max(Decimal("0"), rate.cap_amount - spent)
        matched_amount = min(amount, remaining)
        fallback_amount = amount - matched_amount

    reward_amount, reward_unit = _reward_for(
        matched_amount, rate.rate_multiplier, rate.rate_type
    )
    if fallback_amount:
        if rate.fallback_rate is None:
            warnings.append("The amount over the cap has no explicit fallback rate.")
        else:
            fallback_reward, fallback_unit = _reward_for(
                fallback_amount, rate.fallback_rate, rate.rate_type
            )
            if fallback_unit == reward_unit:
                reward_amount += fallback_reward

    explanation = [
        f"Matched {rate.category.category} at {rate.rate_multiplier} {rate.get_rate_type_display()}.",
    ]
    if rate.booking_channel:
        explanation.append(f"Booking channel: {rate.get_booking_channel_display()}.")
    if rate.booking_portal:
        explanation.append(f"Required portal: {rate.booking_portal}.")
    if fallback_amount:
        explanation.append(
            f"{matched_amount} earns the featured rate and {fallback_amount} is over the cap."
        )

    return RewardMatchResult(
        status="matched",
        reward_rate=rate,
        reward_amount=reward_amount,
        reward_unit=reward_unit,
        matched_amount=matched_amount,
        fallback_amount=fallback_amount,
        explanation=tuple(explanation),
        warnings=tuple(warnings),
    )
