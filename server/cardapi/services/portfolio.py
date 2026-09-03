from dataclasses import dataclass, field, replace
from decimal import Decimal, InvalidOperation
from typing import Mapping

from cardapi.models import (
    CCRewardRate,
    CreditCard,
    RewardCategory,
    RewardProgram,
    SignupBonus,
    StatementCredit,
)
from cardapi.services.comparison import CardComparisonResult, value_reward_match
from cardapi.services.goals import PortfolioGoalSummary, summarize_portfolio_goals
from cardapi.services.rewards import RewardMatchError, RewardMatchResult, match_reward_rate


@dataclass(frozen=True)
class SpendingBucket:
    category: RewardCategory | str
    annual_amount: Decimal
    context: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class StatementCreditUse:
    statement_credit: StatementCredit
    utilization: Decimal


class BonusEligibility:
    ELIGIBLE = "eligible"
    ASSUMED = "assumed"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"

    VALUES = {ELIGIBLE, ASSUMED, INELIGIBLE, UNKNOWN}


@dataclass(frozen=True)
class SignupBonusUse:
    signup_bonus: SignupBonus
    eligibility: str = BonusEligibility.UNKNOWN
    can_meet_minimum_spend: bool | None = None


@dataclass(frozen=True)
class SignupBonusAssessment:
    signup_bonus: SignupBonus | None
    estimated_value: Decimal | None
    included_value: Decimal
    bonus_unit: str | None
    cents_per_point: Decimal | None
    is_included: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioAllocation:
    spending: SpendingBucket
    comparison: CardComparisonResult


@dataclass(frozen=True)
class PortfolioEvaluation:
    cards: tuple[CreditCard, ...]
    allocations: tuple[PortfolioAllocation, ...]
    unresolved_spending: tuple[SpendingBucket, ...]
    annual_spend: Decimal
    estimated_reward_value: Decimal
    estimated_statement_credit_value: Decimal
    recurring_annual_fees: Decimal | None
    first_year_annual_fees: Decimal | None
    recurring_net_value: Decimal | None
    first_year_net_value_before_signup_bonus: Decimal | None
    credits_used: tuple[StatementCreditUse, ...]
    unvalued_perk_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class CandidatePortfolioResult:
    candidate: CreditCard
    portfolio: PortfolioEvaluation
    incremental_recurring_value: Decimal | None
    signup_bonus: SignupBonusAssessment
    first_year_net_value: Decimal | None
    incremental_first_year_value: Decimal | None
    goal_summary: PortfolioGoalSummary | None = None
    incremental_goal_priority: Decimal | None = None
    rank: int | None = None
    first_year_rank: int | None = None
    goal_rank: int | None = None


@dataclass(frozen=True)
class PortfolioAnalysis:
    baseline: PortfolioEvaluation
    candidates: tuple[CandidatePortfolioResult, ...]
    baseline_goal_summary: PortfolioGoalSummary | None = None


_PERIODS_PER_YEAR = {
    StatementCredit.Period.MONTHLY: Decimal("12"),
    StatementCredit.Period.QUARTERLY: Decimal("4"),
    StatementCredit.Period.SEMI_ANNUAL: Decimal("2"),
    StatementCredit.Period.ANNUAL: Decimal("1"),
}

_CAP_PERIODS_PER_YEAR = {
    CCRewardRate.CapPeriod.MONTHLY: Decimal("12"),
    CCRewardRate.CapPeriod.QUARTERLY: Decimal("4"),
    CCRewardRate.CapPeriod.ANNUAL: Decimal("1"),
}


def _decimal(value, name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RewardMatchError(f"{name} must be a number.") from exc
    if result < 0:
        raise RewardMatchError(f"{name} cannot be negative.")
    return result


def _normalize_spending(spending):
    if isinstance(spending, Mapping):
        spending = [
            SpendingBucket(category=category, annual_amount=amount)
            for category, amount in spending.items()
        ]
    normalized = []
    for item in spending:
        if not isinstance(item, SpendingBucket):
            raise TypeError("spending entries must be SpendingBucket instances.")
        normalized.append(
            replace(
                item,
                annual_amount=_decimal(item.annual_amount, "annual_amount"),
                context=dict(item.context),
            )
        )
    return sorted(normalized, key=lambda item: item.annual_amount, reverse=True)


def _reward_for(amount, rate):
    if rate.rate_type == CCRewardRate.RateType.PERCENT_CASHBACK:
        return amount * rate.rate_multiplier / Decimal("100"), "cash"
    return amount * rate.rate_multiplier, "points"


def _annual_match(card, spending, cap_spend_to_date):
    match = match_reward_rate(
        card=card,
        category=spending.category,
        amount=spending.annual_amount,
        category_spend_to_date=Decimal("0"),
        **dict(spending.context),
    )
    rate = match.reward_rate
    if match.status != "matched" or rate is None or rate.cap_amount is None:
        return match

    periods = _CAP_PERIODS_PER_YEAR.get(rate.cap_period, Decimal("1"))
    annual_cap = rate.cap_amount * periods
    already_spent = cap_spend_to_date.get(rate.pk, Decimal("0"))
    remaining = max(Decimal("0"), annual_cap - already_spent)
    matched_amount = min(spending.annual_amount, remaining)
    fallback_amount = spending.annual_amount - matched_amount
    reward_amount, reward_unit = _reward_for(matched_amount, rate)
    warnings = list(match.warnings)
    if rate.cap_period in (
        CCRewardRate.CapPeriod.MONTHLY,
        CCRewardRate.CapPeriod.QUARTERLY,
    ):
        warnings.append(
            "Periodic cap assumes spending is distributed across the year."
        )
    if fallback_amount:
        if rate.fallback_rate is None:
            warnings.append("The amount over the cap has no explicit fallback rate.")
        elif rate.rate_type == CCRewardRate.RateType.PERCENT_CASHBACK:
            reward_amount += fallback_amount * rate.fallback_rate / Decimal("100")
        else:
            reward_amount += fallback_amount * rate.fallback_rate

    return replace(
        match,
        reward_amount=reward_amount,
        reward_unit=reward_unit,
        matched_amount=matched_amount,
        fallback_amount=fallback_amount,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _credit_value(cards, credit_uses):
    card_ids = {card.pk for card in cards}
    total = Decimal("0")
    accepted = []
    warnings = []
    seen = set()
    for use in credit_uses:
        credit = use.statement_credit
        utilization = _decimal(use.utilization, "statement credit utilization")
        if utilization > 1:
            raise RewardMatchError("statement credit utilization cannot exceed 1.")
        if credit.pk in seen:
            raise RewardMatchError("A statement credit can only be supplied once.")
        seen.add(credit.pk)
        if credit.credit_card_id not in card_ids:
            raise RewardMatchError(
                f"{credit.name} does not belong to a card in this portfolio."
            )
        if not credit.is_active or credit.amount is None:
            warnings.append(f"{credit.name} was not valued because it is inactive or has no amount.")
            continue
        periods = _PERIODS_PER_YEAR.get(credit.period)
        if periods is None:
            warnings.append(f"{credit.name} has an unknown period and was not valued.")
            continue
        total += credit.amount * periods * utilization
        accepted.append(replace(use, utilization=utilization))
    return total, tuple(accepted), tuple(warnings)


def evaluate_portfolio(
    *,
    cards,
    spending,
    valuation_strategy="cash",
    custom_cpp=None,
    statement_credit_uses=(),
):
    """Estimate recurring annual value and an explainable card assignment."""
    cards = tuple(dict.fromkeys(cards))
    spending = _normalize_spending(spending)
    cap_spend = {card.pk: {} for card in cards}
    allocations = []
    unresolved = []
    warnings = []

    for bucket in spending:
        comparisons = []
        for card in cards:
            match = _annual_match(card, bucket, cap_spend[card.pk])
            comparison = value_reward_match(
                card=card,
                match=match,
                owned_cards=cards,
                valuation_strategy=valuation_strategy,
                custom_cpp=custom_cpp,
            )
            if comparison.estimated_value is not None and bucket.annual_amount:
                comparison = replace(
                    comparison,
                    effective_return_percent=(
                        comparison.estimated_value
                        / bucket.annual_amount
                        * Decimal("100")
                    ),
                )
            comparisons.append(comparison)

        valued = [item for item in comparisons if item.estimated_value is not None]
        if not valued:
            unresolved.append(bucket)
            continue
        winner = max(valued, key=lambda item: item.estimated_value)
        allocations.append(PortfolioAllocation(spending=bucket, comparison=winner))
        if winner.match.reward_rate and winner.match.reward_rate.cap_amount is not None:
            ledger = cap_spend[winner.card.pk]
            rate_id = winner.match.reward_rate.pk
            ledger[rate_id] = ledger.get(rate_id, Decimal("0")) + bucket.annual_amount
        warnings.extend(winner.match.warnings)

    rewards = sum(
        (allocation.comparison.estimated_value for allocation in allocations),
        Decimal("0"),
    )


    credits, credits_used, credit_warnings = _credit_value(cards, statement_credit_uses)
    warnings.extend(credit_warnings)
    missing_fee_cards = [card.name for card in cards if card.annual_fee is None]
    if missing_fee_cards:
        recurring_fees = None
        first_year_fees = None
        warnings.append(
            "Annual fee is unknown for: " + ", ".join(sorted(missing_fee_cards)) + "."
        )
    else:
        recurring_fees = sum((card.annual_fee for card in cards), Decimal("0"))
        first_year_fees = sum(
            (
                Decimal("0")
                if card.annual_fee_waived_first_year is True
                else card.annual_fee
                for card in cards
            ),
            Decimal("0"),
        )

    # A person with no current cards has a valid $0 baseline. Their spending is
    # unallocated, but it is not a missing-data condition until a card is being
    # evaluated and still cannot value that spending.
    incomplete = (bool(unresolved) and bool(cards)) or recurring_fees is None
    recurring_net = None if incomplete else rewards + credits - recurring_fees
    first_year_net = None if incomplete else rewards + credits - first_year_fees
    if unresolved and cards:
        warnings.append(
            "Net value is unavailable because some spending could not be valued."
        )
    elif unresolved:
        warnings.append("No current cards were available to earn rewards.")

    perk_count = sum(card.perks.filter(is_active=True).count() for card in cards)
    return PortfolioEvaluation(
        cards=cards,
        allocations=tuple(allocations),
        unresolved_spending=tuple(unresolved),
        annual_spend=sum((item.annual_amount for item in spending), Decimal("0")),
        estimated_reward_value=rewards,
        estimated_statement_credit_value=credits,
        recurring_annual_fees=recurring_fees,
        first_year_annual_fees=first_year_fees,
        recurring_net_value=recurring_net,
        first_year_net_value_before_signup_bonus=first_year_net,
        credits_used=credits_used,
        unvalued_perk_count=perk_count,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _bonus_assessment(
    *,
    candidate,
    portfolio_cards,
    valuation_strategy,
    custom_cpp,
    use,
):
    bonus = use.signup_bonus if use else (
        candidate.signup_bonuses.filter(is_active=True)
        .order_by("-last_seen_at", "-pk")
        .first()
    )
    if bonus is None:
        return SignupBonusAssessment(
            signup_bonus=None,
            estimated_value=None,
            included_value=Decimal("0"),
            bonus_unit=None,
            cents_per_point=None,
            is_included=False,
            reasons=("No active signup bonus is available.",),
        )
    if bonus.credit_card_id != candidate.pk:
        raise RewardMatchError(
            f"{bonus.offer_text} does not belong to candidate {candidate.name}."
        )
    if use and use.eligibility not in BonusEligibility.VALUES:
        raise RewardMatchError(
            "bonus eligibility must be eligible, assumed, ineligible, or unknown."
        )

    unit = bonus.bonus_unit or (
        bonus.reward_program.unit if bonus.reward_program else None
    )
    estimated_value = None
    cpp = None
    reasons = []
    if not bonus.is_active:
        reasons.append("The signup offer is not active.")
    if bonus.bonus_amount is None:
        reasons.append("The signup bonus amount is unknown.")
    elif unit == RewardProgram.Unit.CASH:
        estimated_value = bonus.bonus_amount
    elif unit in (RewardProgram.Unit.POINTS, RewardProgram.Unit.MILES):
        if bonus.reward_program is None:
            reasons.append("The signup bonus is not linked to a reward program.")
        else:
            synthetic_match = RewardMatchResult(
                status="matched",
                reward_rate=None,
                reward_amount=bonus.bonus_amount,
                reward_unit="points",
                matched_amount=None,
                fallback_amount=None,
                explanation=("Signup bonus reward amount.",),
                warnings=(),
            )
            valued = value_reward_match(
                card=candidate,
                match=synthetic_match,
                owned_cards=portfolio_cards,
                valuation_strategy=valuation_strategy,
                custom_cpp=custom_cpp,
                reward_program=bonus.reward_program,
            )
            estimated_value = valued.estimated_value
            cpp = valued.cents_per_point
            if estimated_value is None:
                reasons.append(
                    "No value is available for this reward program and strategy."
                )
    else:
        reasons.append("The signup bonus unit is unknown.")

    eligibility = use.eligibility if use else BonusEligibility.UNKNOWN
    can_meet_spend = use.can_meet_minimum_spend if use else None
    if eligibility == BonusEligibility.UNKNOWN:
        reasons.append("Signup-bonus eligibility has not been confirmed.")
    elif eligibility == BonusEligibility.INELIGIBLE:
        reasons.append("The user is not eligible for this signup bonus.")
    elif eligibility == BonusEligibility.ASSUMED:
        reasons.append("Signup-bonus eligibility is assumed, not confirmed.")
    if bonus.minimum_spend is None or bonus.minimum_spend_months is None:
        reasons.append("The minimum-spend requirement or timeframe is unknown.")
    if can_meet_spend is None:
        reasons.append("The user has not confirmed they can meet the minimum spend.")
    elif not can_meet_spend:
        reasons.append("The user cannot meet the minimum spend.")

    is_included = bool(
        bonus.is_active
        and estimated_value is not None
        and eligibility in (BonusEligibility.ELIGIBLE, BonusEligibility.ASSUMED)
        and can_meet_spend is True
        and bonus.minimum_spend is not None
        and bonus.minimum_spend_months is not None
    )
    return SignupBonusAssessment(
        signup_bonus=bonus,
        estimated_value=estimated_value,
        included_value=estimated_value if is_included else Decimal("0"),
        bonus_unit=unit,
        cents_per_point=cpp,
        is_included=is_included,
        reasons=tuple(reasons),
    )


def analyze_candidate_cards(
    *,
    current_cards,
    candidates,
    spending,
    valuation_strategy="cash",
    custom_cpp=None,
    statement_credit_uses=(),
    signup_bonus_uses=(),
    reward_goals=(),
    account_opened_dates=None,
    as_of=None,
):
    """Compare the current portfolio with adding each candidate individually."""
    current_cards = tuple(dict.fromkeys(current_cards))
    candidates = tuple(
        card for card in dict.fromkeys(candidates) if card not in current_cards
    )
    spending = tuple(_normalize_spending(spending))
    current_card_ids = {card.pk for card in current_cards}
    bonus_uses_by_card = {}
    for use in signup_bonus_uses:
        card_id = use.signup_bonus.credit_card_id
        if card_id in bonus_uses_by_card:
            raise RewardMatchError("Only one signup bonus can be evaluated per candidate.")
        bonus_uses_by_card[card_id] = use
    baseline_credit_uses = tuple(
        use
        for use in statement_credit_uses
        if use.statement_credit.credit_card_id in current_card_ids
    )
    baseline = evaluate_portfolio(
        cards=current_cards,
        spending=spending,
        valuation_strategy=valuation_strategy,
        custom_cpp=custom_cpp,
        statement_credit_uses=baseline_credit_uses,
    )
    baseline_goal_summary = None
    if reward_goals:
        baseline_goal_summary = summarize_portfolio_goals(
            cards=current_cards,
            goals=reward_goals,
            account_opened_dates=account_opened_dates,
            as_of=as_of,
        )
    results = []
    for candidate in candidates:
        applicable_credit_uses = tuple(
            use
            for use in statement_credit_uses
            if use.statement_credit.credit_card_id
            in current_card_ids | {candidate.pk}
        )
        portfolio = evaluate_portfolio(
            cards=(*current_cards, candidate),
            spending=spending,
            valuation_strategy=valuation_strategy,
            custom_cpp=custom_cpp,
            statement_credit_uses=applicable_credit_uses,
        )
        bonus = _bonus_assessment(
            candidate=candidate,
            portfolio_cards=(*current_cards, candidate),
            valuation_strategy=valuation_strategy,
            custom_cpp=custom_cpp,
            use=bonus_uses_by_card.get(candidate.pk),
        )
        incremental = None
        if baseline.recurring_net_value is not None and portfolio.recurring_net_value is not None:
            incremental = portfolio.recurring_net_value - baseline.recurring_net_value
        first_year_net = None
        incremental_first_year = None
        if portfolio.first_year_net_value_before_signup_bonus is not None:
            first_year_net = (
                portfolio.first_year_net_value_before_signup_bonus
                + bonus.included_value
            )
        if (
            first_year_net is not None
            and baseline.first_year_net_value_before_signup_bonus is not None
        ):
            incremental_first_year = (
                first_year_net
                - baseline.first_year_net_value_before_signup_bonus
            )
        goal_summary = None
        incremental_goal_priority = None
        if reward_goals:
            goal_summary = summarize_portfolio_goals(
                cards=(*current_cards, candidate),
                goals=reward_goals,
                account_opened_dates=account_opened_dates,
                as_of=as_of,
            )
            incremental_goal_priority = (
                goal_summary.covered_priority
                - baseline_goal_summary.covered_priority
            )
        results.append(
            CandidatePortfolioResult(
                candidate=candidate,
                portfolio=portfolio,
                incremental_recurring_value=incremental,
                signup_bonus=bonus,
                first_year_net_value=first_year_net,
                incremental_first_year_value=incremental_first_year,
                goal_summary=goal_summary,
                incremental_goal_priority=incremental_goal_priority,
            )
        )

    ranked = sorted(
        results,
        key=lambda item: (
            item.incremental_recurring_value is not None,
            item.incremental_recurring_value or Decimal("-Infinity"),
        ),
        reverse=True,
    )
    rank = 0
    final = []
    for item in ranked:
        if item.incremental_recurring_value is not None:
            rank += 1
            item = replace(item, rank=rank)
        final.append(item)

    first_year_rank_by_card = {}
    first_year_rank = 0
    for item in sorted(
        results,
        key=lambda candidate_result: (
            candidate_result.incremental_first_year_value is not None,
            candidate_result.incremental_first_year_value or Decimal("-Infinity"),
        ),
        reverse=True,
    ):
        if item.incremental_first_year_value is not None:
            first_year_rank += 1
            first_year_rank_by_card[item.candidate.pk] = first_year_rank
    final = [
        replace(item, first_year_rank=first_year_rank_by_card.get(item.candidate.pk))
        for item in final
    ]

    goal_rank_by_card = {}
    if reward_goals:
        for index, item in enumerate(
            sorted(
                results,
                key=lambda candidate_result: (
                    candidate_result.incremental_goal_priority,
                    candidate_result.goal_summary.covered_priority,
                ),
                reverse=True,
            ),
            1,
        ):
            goal_rank_by_card[item.candidate.pk] = index
    final = [
        replace(item, goal_rank=goal_rank_by_card.get(item.candidate.pk))
        for item in final
    ]
    return PortfolioAnalysis(
        baseline=baseline,
        candidates=tuple(final),
        baseline_goal_summary=baseline_goal_summary,
    )
