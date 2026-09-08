import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class OwnedCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_cards",
        on_delete=models.CASCADE,
    )
    card = models.ForeignKey(
        "cardapi.CreditCard",
        related_name="+",
        on_delete=models.PROTECT,
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "card"], name="unique_owned_card_per_user"),
        ]

    def __str__(self):
        return f"{self.user}: {self.card}"


class OwnedCardCreditUse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owned_card = models.ForeignKey(
        OwnedCard,
        related_name="credit_uses",
        on_delete=models.CASCADE,
    )
    statement_credit = models.ForeignKey(
        "cardapi.StatementCredit",
        related_name="+",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owned_card", "statement_credit"],
                name="unique_credit_use_per_owned_card",
            ),
        ]

    def __str__(self):
        return f"{self.owned_card}: {self.statement_credit}"


class MonthlyIncome(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="monthly_income",
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: {self.amount}"


class BudgetCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="budget_categories",
        on_delete=models.CASCADE,
    )
    key = models.SlugField(max_length=64)
    label = models.CharField(max_length=100)
    allocated = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=7)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "budget categories"
        constraints = [
            models.UniqueConstraint(fields=["user", "key"], name="unique_budget_category_key_per_user"),
        ]

    def __str__(self):
        return f"{self.user}: {self.label}"


class SpendLogEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="spend_log_entries",
        on_delete=models.CASCADE,
    )
    merchant = models.CharField(max_length=200)
    category = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name_plural = "spend log entries"

    def __str__(self):
        return f"{self.user}: {self.merchant} ({self.amount})"
