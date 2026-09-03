from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation

from cardapi.models import (
    CreditCard,
    RewardProgram,
    RewardProgramUnlock,
    RewardTransferRoute,
)


class RewardGoalError(ValueError):
    """Raised when a reward goal cannot be evaluated safely."""


@dataclass(frozen=True)
class RewardGoal:
    programs: tuple[RewardProgram | str, ...]
    label: str
    priority: Decimal = Decimal("1")


@dataclass(frozen=True)
class GoalAccessOption:
    destination_program: RewardProgram
    method: str
    source_program: RewardProgram
    access_card: CreditCard
    route: RewardTransferRoute | None
    conversion_ratio: Decimal | None
    explanation: tuple[str, ...]


@dataclass(frozen=True)
class CardGoalResult:
    card: CreditCard
    goal: RewardGoal
    status: str
    options: tuple[GoalAccessOption, ...]
    missing_inputs: tuple[str, ...]
    explanation: tuple[str, ...]


@dataclass(frozen=True)
class CardGoalSummary:
    card: CreditCard
    goal_results: tuple[CardGoalResult, ...]
    covered_goal_count: int
    covered_priority: Decimal
    direct_goal_count: int
    rank: int | None = None


@dataclass(frozen=True)
class PortfolioGoalSummary:
    card_results: tuple[CardGoalSummary, ...]
    covered_goals: tuple[RewardGoal, ...]
    unresolved_goals: tuple[RewardGoal, ...]
    covered_priority: Decimal


def _priority(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise RewardGoalError("goal priority must be a number.") from exc
    if result <= 0:
        raise RewardGoalError("goal priority must be greater than zero.")
    return result


def _normalize_goal(goal):
    if not isinstance(goal, RewardGoal):
        raise TypeError("goals must contain RewardGoal instances.")
    if not goal.programs:
        raise RewardGoalError("A reward goal requires at least one program.")
    programs = []
    seen = set()
    for value in goal.programs:
        try:
            program = (
                RewardProgram.objects.get(code=value)
                if isinstance(value, str)
                else value
            )
        except RewardProgram.DoesNotExist as exc:
            raise RewardGoalError(f"Unknown reward program {value!r}.") from exc
        if not program.is_active:
            raise RewardGoalError(f"Reward program {program.name} is inactive.")
        if program.pk not in seen:
            programs.append(program)
            seen.add(program.pk)
    return replace(goal, programs=tuple(programs), priority=_priority(goal.priority))


def _route_ratio(route):
    if route.source_amount is None or route.destination_amount is None:
        return None
    return route.destination_amount / route.source_amount


def _date_eligible(route, as_of):
    return not (
        (route.effective_from and route.effective_from > as_of)
        or (route.effective_through and route.effective_through < as_of)
    )


def _cohort_eligible(route, account_opened_on):
    return not (
        (
            route.account_opened_before
            and account_opened_on >= route.account_opened_before
        )
        or (
            route.account_opened_on_or_after
            and account_opened_on < route.account_opened_on_or_after
        )
    )


def _select_routes(routes, access_card, account_opened_on, as_of):
    current = [route for route in routes if _date_eligible(route, as_of)]
    specific = [route for route in current if route.eligible_card_id == access_card.pk]
    general = [route for route in current if route.eligible_card_id is None]
    if not specific:
        return general, ()

    unconditional = [
        route
        for route in specific
        if not route.account_opened_before and not route.account_opened_on_or_after
    ]
    if unconditional:
        return unconditional, ()
    if account_opened_on is None:
        possible_ratios = {_route_ratio(route) for route in specific}
        if general:
            possible_ratios.update(_route_ratio(route) for route in general)
        if len(possible_ratios) > 1:
            return (), (f"account_opened_on:{access_card.pk}",)
        return specific, ()

    eligible = [
        route for route in specific if _cohort_eligible(route, account_opened_on)
    ]
    return (eligible or general), ()


def _access_cards(card, membership, portfolio_card_ids):
    if membership.can_transfer_partners:
        return ((card, "transfer"),)
    unlocks = (
        RewardProgramUnlock.objects.filter(
            reward_program=membership.reward_program,
            source_card=card,
            required_card_id__in=portfolio_card_ids,
            capability=RewardProgramUnlock.Capability.TRANSFER_PARTNERS,
            is_active=True,
        )
        .select_related("required_card")
        .order_by("required_card__name")
    )
    return tuple((unlock.required_card, "portfolio_unlock") for unlock in unlocks)


def _goal_for_card(card, goal, portfolio_card_ids, account_opened_dates, as_of):
    memberships = list(
        card.reward_program_memberships.filter(
            is_active=True,
            reward_program__is_active=True,
        ).select_related("reward_program")
    )
    options = []
    missing = set()

    for target in goal.programs:
        direct = next(
            (
                membership
                for membership in memberships
                if membership.reward_program_id == target.pk
            ),
            None,
        )
        if direct:
            options.append(
                GoalAccessOption(
                    destination_program=target,
                    method="direct_earn",
                    source_program=target,
                    access_card=card,
                    route=None,
                    conversion_ratio=Decimal("1"),
                    explanation=(f"{card.name} earns {target.name} directly.",),
                )
            )
            continue

        for membership in memberships:
            access_cards = _access_cards(card, membership, portfolio_card_ids)
            if not access_cards:
                continue
            routes = list(
                RewardTransferRoute.objects.filter(
                    source_program=membership.reward_program,
                    destination_program=target,
                    is_active=True,
                    source_program__is_active=True,
                    destination_program__is_active=True,
                ).select_related(
                    "source_program", "destination_program", "eligible_card"
                )
            )
            for access_card, method in access_cards:
                selected, missing_fields = _select_routes(
                    routes,
                    access_card,
                    account_opened_dates.get(access_card.pk),
                    as_of,
                )
                missing.update(missing_fields)
                for route in selected:
                    explanation = [
                        f"{membership.reward_program.name} transfers to {target.name}."
                    ]
                    if method == "portfolio_unlock":
                        explanation.append(
                            f"Transfer access is unlocked by {access_card.name}."
                        )
                    ratio = _route_ratio(route)
                    if ratio is None:
                        explanation.append("The current transfer ratio is not published in this dataset.")
                    else:
                        explanation.append(
                            f"{route.source_amount} source rewards convert to "
                            f"{route.destination_amount} destination rewards."
                        )
                    options.append(
                        GoalAccessOption(
                            destination_program=target,
                            method=method,
                            source_program=membership.reward_program,
                            access_card=access_card,
                            route=route,
                            conversion_ratio=ratio,
                            explanation=tuple(explanation),
                        )
                    )

    unique_options = []
    identities = set()
    for option in options:
        identity = (
            option.destination_program.pk,
            option.method,
            option.source_program.pk,
            option.access_card.pk,
            option.route.pk if option.route else None,
        )
        if identity not in identities:
            unique_options.append(option)
            identities.add(identity)

    if unique_options:
        status = "matched"
        explanation = (f"{card.name} supports the {goal.label} goal.",)
    elif missing:
        status = "needs_information"
        explanation = ("The transfer result depends on account-opening details.",)
    else:
        status = "unavailable"
        explanation = (f"{card.name} has no active route to this goal.",)
    return CardGoalResult(
        card=card,
        goal=goal,
        status=status,
        options=tuple(unique_options),
        missing_inputs=tuple(sorted(missing)),
        explanation=explanation,
    )


def match_reward_goals(
    *,
    cards,
    goals,
    owned_cards=(),
    account_opened_dates=None,
    as_of=None,
):
    """Rank cards by access to explicitly selected loyalty-program goals."""
    cards = tuple(dict.fromkeys(cards))
    owned_cards = tuple(dict.fromkeys(owned_cards))
    goals = tuple(_normalize_goal(goal) for goal in goals)
    as_of = as_of or date.today()
    account_opened_dates = dict(account_opened_dates or {})
    portfolio_card_ids = {card.pk for card in (*cards, *owned_cards)}
    summaries = []

    for card in cards:
        results = tuple(
            _goal_for_card(
                card,
                goal,
                portfolio_card_ids,
                account_opened_dates,
                as_of,
            )
            for goal in goals
        )
        matched = [result for result in results if result.status == "matched"]
        summaries.append(
            CardGoalSummary(
                card=card,
                goal_results=results,
                covered_goal_count=len(matched),
                covered_priority=sum(
                    (result.goal.priority for result in matched), Decimal("0")
                ),
                direct_goal_count=sum(
                    any(option.method == "direct_earn" for option in result.options)
                    for result in matched
                ),
            )
        )

    ranked = sorted(
        summaries,
        key=lambda result: (
            result.covered_priority,
            result.covered_goal_count,
            result.direct_goal_count,
        ),
        reverse=True,
    )
    return [replace(result, rank=index) for index, result in enumerate(ranked, 1)]


def summarize_portfolio_goals(
    *,
    cards,
    goals,
    account_opened_dates=None,
    as_of=None,
):
    cards = tuple(dict.fromkeys(cards))
    goals = tuple(_normalize_goal(goal) for goal in goals)
    results = tuple(
        match_reward_goals(
            cards=cards,
            goals=goals,
            owned_cards=cards,
            account_opened_dates=account_opened_dates,
            as_of=as_of,
        )
    )
    covered = []
    unresolved = []
    for index, goal in enumerate(goals):
        statuses = [result.goal_results[index].status for result in results]
        if "matched" in statuses:
            covered.append(goal)
        elif "needs_information" in statuses:
            unresolved.append(goal)
    return PortfolioGoalSummary(
        card_results=results,
        covered_goals=tuple(covered),
        unresolved_goals=tuple(unresolved),
        covered_priority=sum((goal.priority for goal in covered), Decimal("0")),
    )
