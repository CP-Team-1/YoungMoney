from decimal import Decimal

from cardapi.models import StatementCredit

PERIODS_PER_YEAR = {
    StatementCredit.Period.MONTHLY: Decimal("12"),
    StatementCredit.Period.QUARTERLY: Decimal("4"),
    StatementCredit.Period.SEMI_ANNUAL: Decimal("2"),
    StatementCredit.Period.ANNUAL: Decimal("1"),
}


def annualized_credit_value(credit):
    """Annual dollar value of a statement credit, or None if it can't be valued."""
    if not credit.is_active or credit.amount is None:
        return None
    periods = PERIODS_PER_YEAR.get(credit.period)
    if periods is None:
        return None
    return credit.amount * periods
