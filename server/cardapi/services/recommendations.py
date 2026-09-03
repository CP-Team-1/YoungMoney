from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation

from cardapi.models import CreditCard
from cardapi.services.goals import PortfolioGoalSummary
from cardapi.services.portfolio import (
    PortfolioEvaluation,
    SignupBonusAssessment,
    analyze_candidate_cards,
)
from cardapi.services.rewards import RewardMatchError


class RecommendationPriority:
    ONGOING_VALUE = "ongoing_value"
    FIRST_YEAR_VALUE = "first_year_value"
    GOALS = "goals"

    VALUES = {ONGOING_VALUE, FIRST_YEAR_VALUE, GOALS}


@dataclass(frozen=True)
class RecommendationAction:
    action_type: str
    candidate: CreditCard
    removed_card: CreditCard | None
    portfolio: PortfolioEvaluation
    incremental_recurring_value: Decimal | None
    signup_bonus: SignupBonusAssessment
    first_year_net_value: Decimal | None
    incremental_first_year_value: Decimal | None
    goal_summary: PortfolioGoalSummary | None
    incremental_goal_priority: Decimal | None
    total_annual_fees: Decimal | None
    reasons: tuple[str, ...]
    rank: int | None = None


@dataclass(frozen=True)
class RecommendationScreening:
    candidate_count: int
    evaluated_action_count: int
    excluded_over_budget: int
    excluded_unknown_fee: int
    returned_action_count: int


@dataclass(frozen=True)
class PortfolioRecommendation:
    baseline: PortfolioEvaluation
    baseline_goal_summary: PortfolioGoalSummary | None
    annual_fee_budget: Decimal
    recommendation_priority: str
    status: str
    recommended_action: RecommendationAction | None
    actions: tuple[RecommendationAction, ...]
    screening: RecommendationScreening
    warnings: tuple[str, ...]


def _decimal(value, name):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RewardMatchError(f"{name} must be a number.") from exc
    if result < 0:
        raise RewardMatchError(f"{name} cannot be negative.")
    return result


def _first_year_values(result, baseline):
    portfolio = result.portfolio
    if portfolio.recurring_net_value is None or baseline.recurring_net_value is None:
        return None, None
    fee_savings = (
        result.candidate.annual_fee
        if result.candidate.annual_fee_waived_first_year is True
        else Decimal("0")
    )
    first_year = (
        portfolio.recurring_net_value
        + fee_savings
        + result.signup_bonus.included_value
    )
    return first_year, first_year - baseline.recurring_net_value


def _action_from_result(action_type, result, baseline, baseline_goals, removed_card):
    recurring = None
    if (
        result.portfolio.recurring_net_value is not None
        and baseline.recurring_net_value is not None
    ):
        recurring = result.portfolio.recurring_net_value - baseline.recurring_net_value
    first_year, incremental_first_year = _first_year_values(result, baseline)
    goal_increment = None
    if result.goal_summary is not None and baseline_goals is not None:
        goal_increment = (
            result.goal_summary.covered_priority - baseline_goals.covered_priority
        )

    reasons = []
    if recurring is None:
        reasons.append("Recurring value could not be compared with the current setup.")
    elif recurring > 0:
        reasons.append(
            f"Estimated recurring value improves by ${recurring:.2f} per year."
        )
    elif recurring < 0:
        reasons.append(
            f"Estimated recurring value decreases by ${abs(recurring):.2f} per year."
        )
    else:
        reasons.append("Estimated recurring value is unchanged.")
    if goal_increment is not None:
        if goal_increment > 0:
            reasons.append(
                f"Adds {goal_increment:.4f} weighted reward-goal coverage."
            )
        elif goal_increment < 0:
            reasons.append(
                f"Loses {abs(goal_increment):.4f} weighted reward-goal coverage."
            )
        else:
            reasons.append("Reward-goal coverage is unchanged.")
    if result.signup_bonus.estimated_value is not None:
        if result.signup_bonus.is_included:
            reasons.append("The confirmed signup bonus is included in first-year value.")
        else:
            reasons.append(
                "The signup bonus is shown but not assumed in first-year value."
            )
    if result.candidate.application_rules:
        reasons.append("Review the issuer's application rules before applying.")
    if not result.candidate.recommended_credit_profile:
        reasons.append("The catalog does not verify a recommended credit profile.")

    return RecommendationAction(
        action_type=action_type,
        candidate=result.candidate,
        removed_card=removed_card,
        portfolio=result.portfolio,
        incremental_recurring_value=recurring,
        signup_bonus=result.signup_bonus,
        first_year_net_value=first_year,
        incremental_first_year_value=incremental_first_year,
        goal_summary=result.goal_summary,
        incremental_goal_priority=goal_increment,
        total_annual_fees=result.portfolio.recurring_annual_fees,
        reasons=tuple(reasons),
    )


def _sort_value(value):
    return value if value is not None else Decimal("-Infinity")


def _ranking_key(action, priority):
    recurring = _sort_value(action.incremental_recurring_value)
    first_year = _sort_value(action.incremental_first_year_value)
    goals = _sort_value(action.incremental_goal_priority)
    if priority == RecommendationPriority.FIRST_YEAR_VALUE:
        return first_year, recurring, goals
    if priority == RecommendationPriority.GOALS:
        return goals, recurring, first_year
    return recurring, goals, first_year


def _is_improvement(action, priority):
    if priority == RecommendationPriority.FIRST_YEAR_VALUE:
        return (
            action.incremental_first_year_value is not None
            and action.incremental_first_year_value > 0
        )
    if priority == RecommendationPriority.GOALS:
        return (
            action.incremental_goal_priority is not None
            and action.incremental_goal_priority > 0
        )
    return (
        action.incremental_recurring_value is not None
        and action.incremental_recurring_value > 0
    )


def recommend_portfolio(
    *,
    current_cards,
    candidates,
    spending,
    annual_fee_budget,
    recommendation_priority=RecommendationPriority.ONGOING_VALUE,
    valuation_strategy="cash",
    custom_cpp=None,
    statement_credit_uses=(),
    signup_bonus_uses=(),
    reward_goals=(),
    account_opened_dates=None,
    as_of=None,
    result_limit=10,
):
    """Rank one-card additions and one-for-one replacements without persistence."""
    if recommendation_priority not in RecommendationPriority.VALUES:
        raise RewardMatchError("Unknown recommendation priority.")
    if recommendation_priority == RecommendationPriority.GOALS and not reward_goals:
        raise RewardMatchError("Goal-priority recommendations require at least one goal.")
    budget = _decimal(annual_fee_budget, "annual_fee_budget")
    if not 1 <= result_limit <= 20:
        raise RewardMatchError("result_limit must be between 1 and 20.")

    current_cards = tuple(dict.fromkeys(current_cards))
    candidates = tuple(
        card for card in dict.fromkeys(candidates) if card not in current_cards
    )
    as_of = as_of or date.today()
    opened_dates = dict(account_opened_dates or {})
    for candidate in candidates:
        opened_dates.setdefault(candidate.pk, as_of)

    addition_analysis = analyze_candidate_cards(
        current_cards=current_cards,
        candidates=candidates,
        spending=spending,
        valuation_strategy=valuation_strategy,
        custom_cpp=custom_cpp,
        statement_credit_uses=statement_credit_uses,
        signup_bonus_uses=signup_bonus_uses,
        reward_goals=reward_goals,
        account_opened_dates=opened_dates,
        as_of=as_of,
    )
    baseline = addition_analysis.baseline
    baseline_goals = addition_analysis.baseline_goal_summary
    raw_actions = [
        _action_from_result(
            "add",
            result,
            baseline,
            baseline_goals,
            removed_card=None,
        )
        for result in addition_analysis.candidates
    ]

    for removed_card in current_cards:
        remaining = tuple(card for card in current_cards if card != removed_card)
        replacement_analysis = analyze_candidate_cards(
            current_cards=remaining,
            candidates=candidates,
            spending=spending,
            valuation_strategy=valuation_strategy,
            custom_cpp=custom_cpp,
            statement_credit_uses=statement_credit_uses,
            signup_bonus_uses=signup_bonus_uses,
            reward_goals=reward_goals,
            account_opened_dates=opened_dates,
            as_of=as_of,
        )
        raw_actions.extend(
            _action_from_result(
                "replace",
                result,
                baseline,
                baseline_goals,
                removed_card=removed_card,
            )
            for result in replacement_analysis.candidates
        )

    feasible = []
    excluded_over_budget = 0
    excluded_unknown_fee = 0
    for action in raw_actions:
        if action.total_annual_fees is None:
            excluded_unknown_fee += 1
        elif action.total_annual_fees > budget:
            excluded_over_budget += 1
        else:
            feasible.append(action)

    ranked = sorted(
        feasible,
        key=lambda action: _ranking_key(action, recommendation_priority),
        reverse=True,
    )
    returned = tuple(
        replace(action, rank=index)
        for index, action in enumerate(ranked[:result_limit], 1)
    )
    recommended = next(
        (
            action
            for action in returned
            if _is_improvement(action, recommendation_priority)
        ),
        None,
    )
    baseline_over_budget = bool(
        baseline.recurring_annual_fees is not None
        and baseline.recurring_annual_fees > budget
    )
    if recommended is None and baseline_over_budget and returned:
        recommended = returned[0]
    if recommended:
        result_status = "recommendation_available"
    elif baseline_over_budget and not returned:
        result_status = "no_feasible_recommendation"
    elif (
        returned
        and _ranking_key(returned[0], recommendation_priority)[0]
        == Decimal("-Infinity")
    ):
        result_status = "insufficient_data"
    else:
        result_status = "keep_current_setup"

    warnings = []
    if baseline.recurring_annual_fees is None:
        warnings.append("The current setup has an unknown annual fee.")
    elif baseline_over_budget:
        warnings.append("The current setup exceeds the supplied annual-fee budget.")
    if excluded_unknown_fee:
        warnings.append(
            "Some actions were excluded because total annual fees could not be verified."
        )
    return PortfolioRecommendation(
        baseline=baseline,
        baseline_goal_summary=baseline_goals,
        annual_fee_budget=budget,
        recommendation_priority=recommendation_priority,
        status=result_status,
        recommended_action=recommended,
        actions=returned,
        screening=RecommendationScreening(
            candidate_count=len(candidates),
            evaluated_action_count=len(raw_actions),
            excluded_over_budget=excluded_over_budget,
            excluded_unknown_fee=excluded_unknown_fee,
            returned_action_count=len(returned),
        ),
        warnings=tuple(warnings),
    )
