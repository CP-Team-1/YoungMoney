import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Goal(models.Model):
    goal = models.CharField(
        max_length=100,
        unique=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.goal


class UserGoal(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="goals",
        on_delete=models.CASCADE,
    )

    # Predefined goal type.
    #
    # This is nullable so custom goals can use
    # custom_goal_type instead.
    goal = models.ForeignKey(
        Goal,
        related_name="user_goals",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Used only when the user chooses Other / Custom.
    custom_goal_type = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    name = models.CharField(
        max_length=150,
    )

    target = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01")
            )
        ],
    )

    # Money currently committed to this goal.
    current = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    notes = models.TextField(
        blank=True,
        default="",
    )

    class Meta:
        ordering = [
            "name",
            "id",
        ]

    def __str__(self):
        return f"{self.user}: {self.name}"