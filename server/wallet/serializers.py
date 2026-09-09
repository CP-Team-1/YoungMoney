from decimal import Decimal

from django.utils.text import slugify
from rest_framework import serializers

from cardapi.models import CreditCard, StatementCredit
from cardapi.services.credits import annualized_credit_value

from .models import BudgetCategory, DailyTask, MonthlyIncome, OwnedCard, SpendLogEntry


class OwnedCardSerializer(serializers.ModelSerializer):
    card_slug = serializers.SlugField(source="card.local_slug", read_only=True)
    card_name = serializers.CharField(source="card.name", read_only=True)
    annual_fee = serializers.DecimalField(
        source="card.annual_fee",
        max_digits=10,
        decimal_places=2,
        read_only=True,
        allow_null=True,
    )
    used_credit_ids = serializers.SerializerMethodField()
    effective_annual_fee = serializers.SerializerMethodField()

    class Meta:
        model = OwnedCard
        fields = [
            "id",
            "card_slug",
            "card_name",
            "annual_fee",
            "used_credit_ids",
            "effective_annual_fee",
            "added_at",
        ]
        read_only_fields = fields

    def get_used_credit_ids(self, owned):
        return [use.statement_credit_id for use in owned.credit_uses.all()]

    def get_effective_annual_fee(self, owned):
        if owned.card.annual_fee is None:
            return None

        used_ids = {
            use.statement_credit_id
            for use in owned.credit_uses.all()
        }

        if not used_ids:
            return owned.card.annual_fee

        credits = owned.card.statement_credits.filter(
            is_active=True,
            pk__in=used_ids,
        )

        total_credit_value = sum(
            (
                annualized_credit_value(credit) or Decimal("0")
                for credit in credits
            ),
            Decimal("0"),
        )

        return owned.card.annual_fee - total_credit_value


class OwnedCardCreateSerializer(serializers.Serializer):
    card_slug = serializers.SlugField(max_length=255)

    def validate_card_slug(self, value):
        if not CreditCard.objects.filter(
            local_slug=value,
            issuer__is_active=True,
        ).exists():
            raise serializers.ValidationError(f"Unknown card: {value}.")
        return value


class CreditUseCreateSerializer(serializers.Serializer):
    card_slug = serializers.SlugField(max_length=255)
    statement_credit_id = serializers.IntegerField()

    def validate(self, attrs):
        user = self.context["request"].user

        try:
            owned = OwnedCard.objects.select_related("card").get(
                user=user,
                card__local_slug=attrs["card_slug"],
            )
        except OwnedCard.DoesNotExist:
            raise serializers.ValidationError(
                "Card is not in your wallet."
            )

        try:
            credit = StatementCredit.objects.get(
                pk=attrs["statement_credit_id"],
                credit_card=owned.card,
                is_active=True,
            )
        except StatementCredit.DoesNotExist:
            raise serializers.ValidationError(
                "Unknown credit for this card."
            )

        attrs["owned_card"] = owned
        attrs["statement_credit"] = credit
        return attrs


class MonthlyIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyIncome
        fields = ["amount"]


class BudgetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetCategory
        fields = [
            "id",
            "key",
            "label",
            "allocated",
            "color",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "key",
            "created_at",
        ]


class BudgetCategoryCreateSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=100)
    allocated = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
    )
    color = serializers.CharField(max_length=7)

    def validate_label(self, value):
        label = value.strip()

        if not label:
            raise serializers.ValidationError(
                "Name is required."
            )

        return label

    def validate(self, attrs):
        user = self.context["request"].user
        label = attrs["label"].strip()

        base_key = slugify(label)

        if not base_key:
            raise serializers.ValidationError(
                {"label": "Name is required."}
            )

        if BudgetCategory.objects.filter(
            user=user,
            label__iexact=label,
        ).exists():
            raise serializers.ValidationError(
                {
                    "label":
                    "A category with this name already exists."
                }
            )

        key = base_key
        suffix = 2

        while BudgetCategory.objects.filter(
            user=user,
            key=key,
        ).exists():
            key = f"{base_key}-{suffix}"
            suffix += 1

        attrs["label"] = label
        attrs["key"] = key

        return attrs


class BudgetCategoryUpdateSerializer(serializers.Serializer):
    label = serializers.CharField(
        max_length=100,
        required=False,
    )
    allocated = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
    )
    color = serializers.CharField(
        max_length=7,
        required=False,
    )

    def validate_label(self, value):
        label = value.strip()

        if not label:
            raise serializers.ValidationError(
                "Name is required."
            )

        user = self.context["request"].user
        category = self.instance

        duplicate = BudgetCategory.objects.filter(
            user=user,
            label__iexact=label,
        )

        if category is not None:
            duplicate = duplicate.exclude(pk=category.pk)

        if duplicate.exists():
            raise serializers.ValidationError(
                "A category with this name already exists."
            )

        return label


class SpendLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpendLogEntry
        fields = [
            "id",
            "merchant",
            "category",
            "amount",
            "date",
        ]
        read_only_fields = ["id"]


class DailyTaskSerializer(serializers.ModelSerializer):
    completed = serializers.BooleanField(
        read_only=True,
        default=False,
    )

    class Meta:
        model = DailyTask
        fields = [
            "id",
            "title",
            "order",
            "completed",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "order",
            "completed",
            "created_at",
        ]


class DailyTaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)

    def validate_title(self, value):
        stripped = value.strip()

        if not stripped:
            raise serializers.ValidationError(
                "Title is required."
            )

        return stripped