from decimal import Decimal

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from cardapi.models import (
    CCRewardRate,
    CardRewardProgram,
    CreditCard,
    Issuer,
    Perk,
    RewardCategory,
    RewardProgram,
    RewardTransferRoute,
    SignupBonus,
    StatementCredit,
)


class IssuerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Issuer
        fields = ("slug", "name", "country", "website", "logo_url")


class IssuerCatalogSerializer(IssuerSummarySerializer):
    active_card_count = serializers.IntegerField(read_only=True)

    class Meta(IssuerSummarySerializer.Meta):
        fields = IssuerSummarySerializer.Meta.fields + ("active_card_count",)


class RewardCategorySerializer(serializers.ModelSerializer):
    parent_slug = serializers.SerializerMethodField()

    class Meta:
        model = RewardCategory
        fields = ("slug", "category", "parent_slug")

    def get_parent_slug(self, category):
        return category.parent.slug if category.parent_id else None


class RewardCategoryChildSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="category", read_only=True)
    parent_slug = serializers.SerializerMethodField()

    class Meta:
        model = RewardCategory
        fields = ("slug", "name", "parent_slug")

    def get_parent_slug(self, category):
        return category.parent.slug if category.parent_id else None


class RewardCategoryCatalogSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="category", read_only=True)
    parent_slug = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = RewardCategory
        fields = ("slug", "name", "parent_slug", "children")

    def get_parent_slug(self, category):
        return category.parent.slug if category.parent_id else None

    def get_children(self, category):
        children = getattr(category, "catalog_children", ())
        return RewardCategoryChildSerializer(children, many=True).data


class RewardProgramSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardProgram
        fields = ("code", "name", "unit", "program_type")


class CardRewardProgramSerializer(serializers.ModelSerializer):
    program = RewardProgramSummarySerializer(source="reward_program", read_only=True)

    class Meta:
        model = CardRewardProgram
        fields = (
            "program",
            "is_primary",
            "can_cash_redeem",
            "can_use_travel_portal",
            "can_transfer_partners",
            "can_combine_rewards",
        )


class RewardRateSerializer(serializers.ModelSerializer):
    category = RewardCategorySerializer(read_only=True)

    class Meta:
        model = CCRewardRate
        fields = (
            "category",
            "rate_multiplier",
            "rate_type",
            "cap_amount",
            "cap_period",
            "fallback_rate",
            "is_base_rate",
            "is_rotating",
            "rotating_quarter",
            "rotating_year",
            "notes",
            "booking_channel",
            "booking_portal",
            "geographic_scope",
            "transaction_method",
            "merchant_scope",
            "enrollment_required",
            "minimum_transaction",
            "valid_from",
            "expires_on",
        )


class SignupBonusSerializer(serializers.ModelSerializer):
    reward_program = RewardProgramSummarySerializer(read_only=True)

    class Meta:
        model = SignupBonus
        fields = (
            "offer_text",
            "bonus_amount",
            "bonus_unit",
            "reward_program",
            "minimum_spend",
            "minimum_spend_months",
            "verified_at",
        )


class StatementCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementCredit
        fields = (
            "name",
            "amount",
            "period",
            "eligible_merchants",
            "enrollment_required",
            "notes",
            "verified_at",
        )


class PerkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perk
        fields = (
            "perk_type",
            "name",
            "value",
            "period",
            "partner",
            "details",
            "enrollment_required",
            "spend_requirement",
            "expires_on",
            "geographic_scope",
            "is_complimentary",
            "coverage_type",
            "benefit_limit",
            "recommendation_notes",
            "verified_at",
        )


class RewardTransferRouteSerializer(serializers.ModelSerializer):
    source_program = RewardProgramSummarySerializer(read_only=True)
    destination_program = RewardProgramSummarySerializer(read_only=True)
    eligible_card_slug = serializers.CharField(
        source="eligible_card.local_slug", read_only=True
    )

    class Meta:
        model = RewardTransferRoute
        fields = (
            "source_program",
            "destination_program",
            "eligible_card_slug",
            "source_amount",
            "destination_amount",
            "minimum_transfer",
            "transfer_increment",
            "effective_from",
            "effective_through",
            "account_opened_before",
            "account_opened_on_or_after",
            "notes",
            "verified_at",
        )


class CreditCardListSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source="local_slug", read_only=True)
    issuer = IssuerSummarySerializer(read_only=True)

    class Meta:
        model = CreditCard
        fields = (
            "slug",
            "name",
            "issuer",
            "network",
            "card_type",
            "product_family",
            "recommended_credit_profile",
            "annual_fee",
            "annual_fee_waived_first_year",
            "foreign_transaction_fee",
            "reward_currency",
            "reward_currency_name",
            "is_discontinued",
            "product_url",
        )


class CreditCardDetailSerializer(CreditCardListSerializer):
    reward_rates = serializers.SerializerMethodField()
    reward_programs = serializers.SerializerMethodField()
    signup_bonuses = serializers.SerializerMethodField()
    statement_credits = serializers.SerializerMethodField()
    perks = serializers.SerializerMethodField()
    transfer_partners = serializers.SerializerMethodField()

    class Meta(CreditCardListSerializer.Meta):
        fields = CreditCardListSerializer.Meta.fields + (
            "credit_score_min",
            "application_rules",
            "official_page_verified_at",
            "reward_programs",
            "reward_rates",
            "signup_bonuses",
            "statement_credits",
            "perks",
            "transfer_partners",
        )

    def get_reward_rates(self, card):
        rates = card.reward_rates.filter(is_active=True).select_related(
            "category", "category__parent"
        ).order_by("category__category", "-rate_multiplier")
        return RewardRateSerializer(rates, many=True).data

    def get_reward_programs(self, card):
        memberships = card.reward_program_memberships.filter(
            is_active=True, reward_program__is_active=True
        ).select_related("reward_program").order_by("-is_primary", "reward_program__name")
        return CardRewardProgramSerializer(memberships, many=True).data

    def get_signup_bonuses(self, card):
        bonuses = card.signup_bonuses.filter(is_active=True).select_related(
            "reward_program"
        ).order_by("-verified_at", "-first_seen_at")
        return SignupBonusSerializer(bonuses, many=True).data

    def get_statement_credits(self, card):
        credits = card.statement_credits.filter(is_active=True).order_by("name")
        return StatementCreditSerializer(credits, many=True).data

    def get_perks(self, card):
        perks = card.perks.filter(is_active=True).order_by("name")
        return PerkSerializer(perks, many=True).data

    def get_transfer_partners(self, card):
        source_program_ids = card.reward_program_memberships.filter(
            is_active=True,
            can_transfer_partners=True,
            reward_program__is_active=True,
        ).values_list("reward_program_id", flat=True)
        today = timezone.localdate()
        routes = (
            RewardTransferRoute.objects.filter(
                source_program_id__in=source_program_ids,
                source_program__is_active=True,
                destination_program__is_active=True,
                is_active=True,
            )
            .filter(Q(eligible_card__isnull=True) | Q(eligible_card=card))
            .filter(Q(effective_from__isnull=True) | Q(effective_from__lte=today))
            .filter(Q(effective_through__isnull=True) | Q(effective_through__gte=today))
            .select_related("source_program", "destination_program", "eligible_card")
            .order_by("destination_program__name", "eligible_card_id", "source_key")
        )
        return RewardTransferRouteSerializer(routes, many=True).data


class CardComparisonRequestSerializer(serializers.Serializer):
    card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        min_length=2,
        max_length=20,
        allow_empty=False,
    )
    owned_card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        max_length=20,
        allow_empty=True,
        required=False,
        default=list,
    )
    category_slug = serializers.SlugField(max_length=255)
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    valuation_strategy = serializers.ChoiceField(
        choices=("cash", "travel_portal", "transfer", "user"),
        default="cash",
    )
    custom_cpp = serializers.DictField(
        child=serializers.DecimalField(
            max_digits=10,
            decimal_places=4,
            min_value=Decimal("0.0001"),
        ),
        required=False,
        default=dict,
    )
    purchase_date = serializers.DateField(required=False)
    booking_channel = serializers.ChoiceField(
        choices=CCRewardRate.BookingChannel.choices,
        required=False,
    )
    booking_portal = serializers.CharField(max_length=255, required=False)
    geographic_scope = serializers.CharField(max_length=255, required=False)
    transaction_method = serializers.ChoiceField(
        choices=CCRewardRate.TransactionMethod.choices,
        required=False,
    )
    merchant_eligible = serializers.BooleanField(required=False)
    enrolled = serializers.BooleanField(required=False)
    category_spend_to_date = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
    )

    def validate_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Card slugs must be unique.")
        return slugs

    def validate_owned_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Owned card slugs must be unique.")
        return slugs

    def validate_custom_cpp(self, values):
        unknown = set(values) - set(
            RewardProgram.objects.filter(
                code__in=values,
                is_active=True,
            ).values_list("code", flat=True)
        )
        if unknown:
            raise serializers.ValidationError(
                f"Unknown active reward programs: {', '.join(sorted(unknown))}."
            )
        return values

    def validate(self, attrs):
        if attrs["custom_cpp"] and attrs["valuation_strategy"] not in {
            "transfer",
            "user",
        }:
            raise serializers.ValidationError(
                {"custom_cpp": "Custom point values require transfer or user valuation."}
            )
        return attrs


class ComparisonCardSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source="local_slug", read_only=True)

    class Meta:
        model = CreditCard
        fields = ("slug", "name")


class CardComparisonResultSerializer(serializers.Serializer):
    card = CreditCardListSerializer(read_only=True)
    rank = serializers.IntegerField(allow_null=True)
    match_status = serializers.CharField(source="match.status")
    matched_reward_rate = RewardRateSerializer(
        source="match.reward_rate",
        allow_null=True,
        read_only=True,
    )
    reward_amount = serializers.DecimalField(
        source="match.reward_amount",
        max_digits=18,
        decimal_places=4,
        allow_null=True,
    )
    reward_unit = serializers.CharField(source="match.reward_unit", allow_null=True)
    matched_amount = serializers.DecimalField(
        source="match.matched_amount",
        max_digits=14,
        decimal_places=2,
        allow_null=True,
    )
    fallback_amount = serializers.DecimalField(
        source="match.fallback_amount",
        max_digits=14,
        decimal_places=2,
        allow_null=True,
    )
    reward_program_code = serializers.CharField(allow_null=True)
    valuation_strategy = serializers.CharField()
    cents_per_point = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        allow_null=True,
    )
    estimated_value = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        allow_null=True,
    )
    effective_return_percent = serializers.DecimalField(
        max_digits=18,
        decimal_places=4,
        allow_null=True,
    )
    unlocked_by = ComparisonCardSerializer(allow_null=True, read_only=True)
    explanation = serializers.ListField(
        source="match.explanation", child=serializers.CharField()
    )
    warnings = serializers.ListField(
        source="match.warnings", child=serializers.CharField()
    )
    missing_inputs = serializers.ListField(
        source="match.missing_inputs", child=serializers.CharField()
    )


class PortfolioSpendingRequestSerializer(serializers.Serializer):
    category_slug = serializers.SlugField(max_length=255)
    annual_amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    booking_channel = serializers.ChoiceField(
        choices=CCRewardRate.BookingChannel.choices,
        required=False,
    )
    booking_portal = serializers.CharField(max_length=255, required=False)
    geographic_scope = serializers.CharField(max_length=255, required=False)
    transaction_method = serializers.ChoiceField(
        choices=CCRewardRate.TransactionMethod.choices,
        required=False,
    )
    merchant_eligible = serializers.BooleanField(required=False)
    enrolled = serializers.BooleanField(required=False)


class StatementCreditUseRequestSerializer(serializers.Serializer):
    card_slug = serializers.SlugField(max_length=255)
    credit_name = serializers.CharField(max_length=255)
    utilization = serializers.DecimalField(
        max_digits=5,
        decimal_places=4,
        min_value=Decimal("0"),
        max_value=Decimal("1"),
    )


class PortfolioEvaluationRequestSerializer(serializers.Serializer):
    card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        min_length=1,
        max_length=20,
        allow_empty=False,
    )
    spending = PortfolioSpendingRequestSerializer(
        many=True,
        allow_empty=False,
        max_length=100,
    )
    valuation_strategy = serializers.ChoiceField(
        choices=("cash", "travel_portal", "transfer", "user"),
        default="cash",
    )
    custom_cpp = serializers.DictField(
        child=serializers.DecimalField(
            max_digits=10,
            decimal_places=4,
            min_value=Decimal("0.0001"),
        ),
        required=False,
        default=dict,
    )
    statement_credit_uses = StatementCreditUseRequestSerializer(
        many=True,
        required=False,
        default=list,
        max_length=100,
    )

    def validate_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Card slugs must be unique.")
        return slugs

    def validate_custom_cpp(self, values):
        unknown = set(values) - set(
            RewardProgram.objects.filter(
                code__in=values,
                is_active=True,
            ).values_list("code", flat=True)
        )
        if unknown:
            raise serializers.ValidationError(
                f"Unknown active reward programs: {', '.join(sorted(unknown))}."
            )
        return values

    def validate_statement_credit_uses(self, uses):
        identities = [(item["card_slug"], item["credit_name"]) for item in uses]
        if len(identities) != len(set(identities)):
            raise serializers.ValidationError(
                "A statement credit can only be supplied once."
            )
        return uses

    def validate(self, attrs):
        if attrs["custom_cpp"] and attrs["valuation_strategy"] not in {
            "transfer",
            "user",
        }:
            raise serializers.ValidationError(
                {"custom_cpp": "Custom point values require transfer or user valuation."}
            )
        portfolio_slugs = set(attrs["card_slugs"])
        outside_portfolio = sorted(
            {
                item["card_slug"]
                for item in attrs["statement_credit_uses"]
                if item["card_slug"] not in portfolio_slugs
            }
        )
        if outside_portfolio:
            raise serializers.ValidationError(
                {
                    "statement_credit_uses": (
                        "Credits must belong to a portfolio card. Unknown portfolio "
                        f"cards: {', '.join(outside_portfolio)}."
                    )
                }
            )
        return attrs


class PortfolioSpendingResultSerializer(serializers.Serializer):
    category_slug = serializers.CharField(source="category.slug")
    category_name = serializers.CharField(source="category.category")
    annual_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    context = serializers.DictField()


class StatementCreditUseResultSerializer(serializers.Serializer):
    card = ComparisonCardSerializer(source="statement_credit.credit_card")
    credit_name = serializers.CharField(source="statement_credit.name")
    utilization = serializers.DecimalField(max_digits=5, decimal_places=4)


class PortfolioAllocationSerializer(serializers.Serializer):
    spending = PortfolioSpendingResultSerializer()
    comparison = CardComparisonResultSerializer()


class PortfolioEvaluationResultSerializer(serializers.Serializer):
    cards = CreditCardListSerializer(many=True)
    allocations = PortfolioAllocationSerializer(many=True)
    unresolved_spending = PortfolioSpendingResultSerializer(many=True)
    annual_spend = serializers.DecimalField(max_digits=18, decimal_places=2)
    estimated_reward_value = serializers.DecimalField(
        max_digits=18, decimal_places=4
    )
    estimated_statement_credit_value = serializers.DecimalField(
        max_digits=18, decimal_places=4
    )
    recurring_annual_fees = serializers.DecimalField(
        max_digits=18, decimal_places=2, allow_null=True
    )
    first_year_annual_fees = serializers.DecimalField(
        max_digits=18, decimal_places=2, allow_null=True
    )
    recurring_net_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    first_year_net_value_before_signup_bonus = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    credits_used = StatementCreditUseResultSerializer(many=True)
    unvalued_perk_count = serializers.IntegerField()
    warnings = serializers.ListField(child=serializers.CharField())


class SignupBonusUseRequestSerializer(serializers.Serializer):
    card_slug = serializers.SlugField(max_length=255)
    eligibility = serializers.ChoiceField(
        choices=("eligible", "assumed", "ineligible", "unknown")
    )
    can_meet_minimum_spend = serializers.BooleanField(allow_null=True)


class CandidateAnalysisRequestSerializer(serializers.Serializer):
    current_card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        max_length=20,
        allow_empty=True,
        required=False,
        default=list,
    )
    candidate_card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        min_length=1,
        max_length=20,
        allow_empty=False,
    )
    spending = PortfolioSpendingRequestSerializer(
        many=True,
        allow_empty=False,
        max_length=100,
    )
    valuation_strategy = serializers.ChoiceField(
        choices=("cash", "travel_portal", "transfer", "user"),
        default="cash",
    )
    custom_cpp = serializers.DictField(
        child=serializers.DecimalField(
            max_digits=10,
            decimal_places=4,
            min_value=Decimal("0.0001"),
        ),
        required=False,
        default=dict,
    )
    statement_credit_uses = StatementCreditUseRequestSerializer(
        many=True,
        required=False,
        default=list,
        max_length=100,
    )
    signup_bonus_uses = SignupBonusUseRequestSerializer(
        many=True,
        required=False,
        default=list,
        max_length=20,
    )

    def validate_current_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Current card slugs must be unique.")
        return slugs

    def validate_candidate_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Candidate card slugs must be unique.")
        return slugs

    def validate_custom_cpp(self, values):
        unknown = set(values) - set(
            RewardProgram.objects.filter(
                code__in=values,
                is_active=True,
            ).values_list("code", flat=True)
        )
        if unknown:
            raise serializers.ValidationError(
                f"Unknown active reward programs: {', '.join(sorted(unknown))}."
            )
        return values

    def validate_statement_credit_uses(self, uses):
        identities = [(item["card_slug"], item["credit_name"]) for item in uses]
        if len(identities) != len(set(identities)):
            raise serializers.ValidationError(
                "A statement credit can only be supplied once."
            )
        return uses

    def validate_signup_bonus_uses(self, uses):
        slugs = [item["card_slug"] for item in uses]
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError(
                "Only one signup-bonus assumption is allowed per candidate."
            )
        return uses

    def validate(self, attrs):
        current = set(attrs["current_card_slugs"])
        candidates = set(attrs["candidate_card_slugs"])
        overlap = sorted(current & candidates)
        if overlap:
            raise serializers.ValidationError(
                {
                    "candidate_card_slugs": (
                        "Candidates cannot already be in the current portfolio: "
                        f"{', '.join(overlap)}."
                    )
                }
            )
        if attrs["custom_cpp"] and attrs["valuation_strategy"] not in {
            "transfer",
            "user",
        }:
            raise serializers.ValidationError(
                {"custom_cpp": "Custom point values require transfer or user valuation."}
            )
        allowed_credit_cards = current | candidates
        invalid_credit_cards = sorted(
            {
                item["card_slug"]
                for item in attrs["statement_credit_uses"]
                if item["card_slug"] not in allowed_credit_cards
            }
        )
        if invalid_credit_cards:
            raise serializers.ValidationError(
                {
                    "statement_credit_uses": (
                        "Credits must belong to a current or candidate card: "
                        f"{', '.join(invalid_credit_cards)}."
                    )
                }
            )
        invalid_bonus_cards = sorted(
            {
                item["card_slug"]
                for item in attrs["signup_bonus_uses"]
                if item["card_slug"] not in candidates
            }
        )
        if invalid_bonus_cards:
            raise serializers.ValidationError(
                {
                    "signup_bonus_uses": (
                        "Signup-bonus assumptions must belong to candidates: "
                        f"{', '.join(invalid_bonus_cards)}."
                    )
                }
            )
        return attrs


class SignupBonusAssessmentSerializer(serializers.Serializer):
    signup_bonus = SignupBonusSerializer(allow_null=True)
    estimated_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    included_value = serializers.DecimalField(max_digits=18, decimal_places=4)
    bonus_unit = serializers.CharField(allow_null=True)
    cents_per_point = serializers.DecimalField(
        max_digits=10, decimal_places=4, allow_null=True
    )
    is_included = serializers.BooleanField()
    reasons = serializers.ListField(child=serializers.CharField())


class CandidatePortfolioResultSerializer(serializers.Serializer):
    candidate = CreditCardListSerializer()
    portfolio = PortfolioEvaluationResultSerializer()
    incremental_recurring_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    signup_bonus = SignupBonusAssessmentSerializer()
    first_year_net_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    incremental_first_year_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    rank = serializers.IntegerField(allow_null=True)
    first_year_rank = serializers.IntegerField(allow_null=True)


class CandidateAnalysisResultSerializer(serializers.Serializer):
    baseline = PortfolioEvaluationResultSerializer()
    candidates = CandidatePortfolioResultSerializer(many=True)


class RewardGoalRequestItemSerializer(serializers.Serializer):
    label = serializers.CharField(max_length=255)
    program_codes = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        min_length=1,
        max_length=20,
        allow_empty=False,
    )
    priority = serializers.DecimalField(
        max_digits=10,
        decimal_places=4,
        min_value=Decimal("0.0001"),
        default=Decimal("1"),
    )

    def validate_program_codes(self, codes):
        if len(codes) != len(set(codes)):
            raise serializers.ValidationError("Program codes must be unique.")
        return codes


class RewardGoalMatchRequestSerializer(serializers.Serializer):
    card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        min_length=1,
        max_length=20,
        allow_empty=False,
    )
    owned_card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        max_length=20,
        allow_empty=True,
        required=False,
        default=list,
    )
    goals = RewardGoalRequestItemSerializer(
        many=True,
        allow_empty=False,
        max_length=20,
    )
    account_opened_dates = serializers.DictField(
        child=serializers.DateField(),
        required=False,
        default=dict,
    )
    as_of = serializers.DateField(required=False, default=timezone.localdate)

    def validate_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Card slugs must be unique.")
        return slugs

    def validate_owned_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Owned card slugs must be unique.")
        return slugs

    def validate_goals(self, goals):
        labels = [goal["label"].strip().casefold() for goal in goals]
        if len(labels) != len(set(labels)):
            raise serializers.ValidationError("Goal labels must be unique.")
        return goals

    def validate(self, attrs):
        known_slugs = set(attrs["card_slugs"]) | set(attrs["owned_card_slugs"])
        unknown_date_slugs = sorted(set(attrs["account_opened_dates"]) - known_slugs)
        if unknown_date_slugs:
            raise serializers.ValidationError(
                {
                    "account_opened_dates": (
                        "Dates must belong to an evaluated or owned card: "
                        f"{', '.join(unknown_date_slugs)}."
                    )
                }
            )
        future_dates = sorted(
            slug
            for slug, opened_on in attrs["account_opened_dates"].items()
            if opened_on > attrs["as_of"]
        )
        if future_dates:
            raise serializers.ValidationError(
                {
                    "account_opened_dates": (
                        "Account-opening dates cannot be after as_of: "
                        f"{', '.join(future_dates)}."
                    )
                }
            )
        return attrs


class RewardGoalDefinitionSerializer(serializers.Serializer):
    label = serializers.CharField()
    priority = serializers.DecimalField(max_digits=10, decimal_places=4)
    programs = RewardProgramSummarySerializer(many=True)


class GoalAccessOptionSerializer(serializers.Serializer):
    destination_program = RewardProgramSummarySerializer()
    method = serializers.CharField()
    source_program = RewardProgramSummarySerializer()
    access_card = ComparisonCardSerializer()
    route = RewardTransferRouteSerializer(allow_null=True)
    conversion_ratio = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        allow_null=True,
    )
    explanation = serializers.ListField(child=serializers.CharField())


class CardGoalResultSerializer(serializers.Serializer):
    goal = RewardGoalDefinitionSerializer()
    status = serializers.CharField()
    options = GoalAccessOptionSerializer(many=True)
    missing_inputs = serializers.SerializerMethodField()
    explanation = serializers.ListField(child=serializers.CharField())

    def get_missing_inputs(self, result):
        slugs_by_pk = self.context.get("card_slugs_by_pk", {})
        translated = []
        for value in result.missing_inputs:
            prefix, separator, raw_pk = value.partition(":")
            if prefix == "account_opened_on" and separator:
                try:
                    slug = slugs_by_pk.get(int(raw_pk))
                except ValueError:
                    slug = None
                if slug:
                    translated.append(f"account_opened_dates.{slug}")
                    continue
            translated.append(value)
        return translated


class CardGoalSummarySerializer(serializers.Serializer):
    card = CreditCardListSerializer()
    goal_results = serializers.SerializerMethodField()
    covered_goal_count = serializers.IntegerField()
    covered_priority = serializers.DecimalField(max_digits=18, decimal_places=4)
    direct_goal_count = serializers.IntegerField()
    rank = serializers.IntegerField(allow_null=True)

    def get_goal_results(self, summary):
        return CardGoalResultSerializer(
            summary.goal_results,
            many=True,
            context=self.context,
        ).data


class PortfolioGoalAggregateSerializer(serializers.Serializer):
    covered_goals = RewardGoalDefinitionSerializer(many=True)
    unresolved_goals = RewardGoalDefinitionSerializer(many=True)
    covered_priority = serializers.DecimalField(max_digits=18, decimal_places=4)


class PortfolioRecommendationRequestSerializer(serializers.Serializer):
    current_card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        max_length=20,
        allow_empty=True,
        required=False,
        default=list,
    )
    spending = PortfolioSpendingRequestSerializer(
        many=True,
        allow_empty=False,
        max_length=100,
    )
    goals = RewardGoalRequestItemSerializer(
        many=True,
        allow_empty=True,
        max_length=20,
        required=False,
        default=list,
    )
    annual_fee_budget = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
    )
    recommendation_priority = serializers.ChoiceField(
        choices=("ongoing_value", "first_year_value", "goals"),
        default="ongoing_value",
    )
    valuation_strategy = serializers.ChoiceField(
        choices=("cash", "travel_portal", "transfer", "user"),
        default="cash",
    )
    custom_cpp = serializers.DictField(
        child=serializers.DecimalField(
            max_digits=10,
            decimal_places=4,
            min_value=Decimal("0.0001"),
        ),
        required=False,
        default=dict,
    )
    credit_profile = serializers.ChoiceField(
        choices=CreditCard.CreditProfile.choices,
        required=False,
        allow_null=True,
    )
    country = serializers.RegexField(
        regex=r"^[A-Za-z]{2}$",
        default="US",
    )
    allowed_card_types = serializers.ListField(
        child=serializers.ChoiceField(choices=CreditCard.CardType.choices),
        min_length=1,
        max_length=4,
        allow_empty=False,
        required=False,
        default=lambda: [CreditCard.CardType.PERSONAL],
    )
    issuer_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        min_length=1,
        max_length=20,
        allow_empty=False,
        required=False,
        default=list,
    )
    excluded_card_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255),
        max_length=100,
        allow_empty=True,
        required=False,
        default=list,
    )
    account_opened_dates = serializers.DictField(
        child=serializers.DateField(),
        required=False,
        default=dict,
    )
    statement_credit_uses = StatementCreditUseRequestSerializer(
        many=True,
        required=False,
        default=list,
        max_length=100,
    )
    signup_bonus_uses = SignupBonusUseRequestSerializer(
        many=True,
        required=False,
        default=list,
        max_length=100,
    )
    result_limit = serializers.IntegerField(min_value=1, max_value=20, default=10)
    as_of = serializers.DateField(required=False, default=timezone.localdate)

    def validate_current_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Current card slugs must be unique.")
        return slugs

    def validate_allowed_card_types(self, card_types):
        if len(card_types) != len(set(card_types)):
            raise serializers.ValidationError("Allowed card types must be unique.")
        return card_types

    def validate_country(self, country):
        return country.upper()

    def validate_excluded_card_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Excluded card slugs must be unique.")
        return slugs

    def validate_issuer_slugs(self, slugs):
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError("Issuer slugs must be unique.")
        return slugs

    def validate_goals(self, goals):
        labels = [goal["label"].strip().casefold() for goal in goals]
        if len(labels) != len(set(labels)):
            raise serializers.ValidationError("Goal labels must be unique.")
        return goals

    def validate_custom_cpp(self, values):
        unknown = set(values) - set(
            RewardProgram.objects.filter(
                code__in=values,
                is_active=True,
            ).values_list("code", flat=True)
        )
        if unknown:
            raise serializers.ValidationError(
                f"Unknown active reward programs: {', '.join(sorted(unknown))}."
            )
        return values

    def validate_statement_credit_uses(self, uses):
        identities = [(item["card_slug"], item["credit_name"]) for item in uses]
        if len(identities) != len(set(identities)):
            raise serializers.ValidationError(
                "A statement credit can only be supplied once."
            )
        return uses

    def validate_signup_bonus_uses(self, uses):
        slugs = [item["card_slug"] for item in uses]
        if len(slugs) != len(set(slugs)):
            raise serializers.ValidationError(
                "Only one signup-bonus assumption is allowed per candidate."
            )
        return uses

    def validate(self, attrs):
        current = set(attrs["current_card_slugs"])
        if attrs["recommendation_priority"] == "goals" and not attrs["goals"]:
            raise serializers.ValidationError(
                {"goals": "Goal-priority recommendations require at least one goal."}
            )
        if attrs["custom_cpp"] and attrs["valuation_strategy"] not in {
            "transfer",
            "user",
        }:
            raise serializers.ValidationError(
                {"custom_cpp": "Custom point values require transfer or user valuation."}
            )
        invalid_dates = sorted(set(attrs["account_opened_dates"]) - current)
        if invalid_dates:
            raise serializers.ValidationError(
                {
                    "account_opened_dates": (
                        "Dates must belong to current cards: "
                        f"{', '.join(invalid_dates)}."
                    )
                }
            )
        future_dates = sorted(
            slug
            for slug, opened_on in attrs["account_opened_dates"].items()
            if opened_on > attrs["as_of"]
        )
        if future_dates:
            raise serializers.ValidationError(
                {
                    "account_opened_dates": (
                        "Account-opening dates cannot be after as_of: "
                        f"{', '.join(future_dates)}."
                    )
                }
            )
        outside_portfolio = sorted(
            {
                item["card_slug"]
                for item in attrs["statement_credit_uses"]
                if item["card_slug"] not in current
            }
        )
        if outside_portfolio:
            raise serializers.ValidationError(
                {
                    "statement_credit_uses": (
                        "Credits must belong to current cards: "
                        f"{', '.join(outside_portfolio)}."
                    )
                }
            )
        current_bonus_slugs = sorted(
            item["card_slug"]
            for item in attrs["signup_bonus_uses"]
            if item["card_slug"] in current
        )
        if current_bonus_slugs:
            raise serializers.ValidationError(
                {
                    "signup_bonus_uses": (
                        "Signup-bonus assumptions must belong to new candidates: "
                        f"{', '.join(current_bonus_slugs)}."
                    )
                }
            )
        return attrs


class RecommendationGoalSummarySerializer(PortfolioGoalAggregateSerializer):
    card_results = CardGoalSummarySerializer(many=True)


class RecommendationActionSerializer(serializers.Serializer):
    action_type = serializers.CharField()
    candidate = CreditCardListSerializer()
    removed_card = CreditCardListSerializer(allow_null=True)
    portfolio = PortfolioEvaluationResultSerializer()
    incremental_recurring_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    signup_bonus = SignupBonusAssessmentSerializer()
    first_year_net_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    incremental_first_year_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    goal_summary = RecommendationGoalSummarySerializer(allow_null=True)
    incremental_goal_priority = serializers.DecimalField(
        max_digits=18, decimal_places=4, allow_null=True
    )
    total_annual_fees = serializers.DecimalField(max_digits=18, decimal_places=2)
    reasons = serializers.ListField(child=serializers.CharField())
    rank = serializers.IntegerField(allow_null=True)


class RecommendationScreeningSerializer(serializers.Serializer):
    candidate_count = serializers.IntegerField()
    evaluated_action_count = serializers.IntegerField()
    excluded_over_budget = serializers.IntegerField()
    excluded_unknown_fee = serializers.IntegerField()
    returned_action_count = serializers.IntegerField()


class PortfolioRecommendationResultSerializer(serializers.Serializer):
    baseline = PortfolioEvaluationResultSerializer()
    baseline_goal_summary = RecommendationGoalSummarySerializer(allow_null=True)
    annual_fee_budget = serializers.DecimalField(max_digits=18, decimal_places=2)
    recommendation_priority = serializers.CharField()
    status = serializers.CharField()
    recommended_action = RecommendationActionSerializer(allow_null=True)
    actions = RecommendationActionSerializer(many=True)
    screening = RecommendationScreeningSerializer()
    warnings = serializers.ListField(child=serializers.CharField())
