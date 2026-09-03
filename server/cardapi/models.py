from django.db import models


class TimestampedModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Issuer(TimestampedModel):
    cardapi_id = models.UUIDField(blank=True, null=True, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=2, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    curated_sources = models.JSONField(blank=True, default=dict)

    def __str__(self):
        return self.name


class RewardCategory(TimestampedModel):
    slug = models.SlugField(max_length=255, unique=True)
    category = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    is_user_facing = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.category


class RewardCategoryAlias(TimestampedModel):
    category = models.ForeignKey(
        RewardCategory,
        related_name="aliases",
        on_delete=models.CASCADE,
    )
    source = models.CharField(max_length=32)
    alias = models.SlugField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("source", "alias"),
                name="unique_reward_category_source_alias",
            )
        ]

    def __str__(self):
        return f"{self.source}: {self.alias} → {self.category.category}"


class CreditCard(TimestampedModel):
    class Network(models.TextChoices):
        VISA = "VISA", "Visa"
        MASTERCARD = "MC", "Mastercard"
        AMEX = "AMEX", "American Express"
        DISCOVER = "DISCOVER", "Discover"

    class CardType(models.TextChoices):
        PERSONAL = "personal", "Personal"
        BUSINESS = "business", "Business"
        STUDENT = "student", "Student"
        SECURED = "secured", "Secured"

    class CreditProfile(models.TextChoices):
        EXCELLENT = "excellent", "Excellent"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        STUDENT = "student", "Student"

    cardapi_id = models.UUIDField(blank=True, null=True, unique=True)
    local_slug = models.SlugField(max_length=255, unique=True)
    cardapi_slug = models.SlugField(max_length=255, blank=True, null=True, unique=True)
    issuer = models.ForeignKey(
        Issuer,
        related_name="credit_cards",
        on_delete=models.PROTECT,
    )
    name = models.CharField(max_length=255)
    network = models.CharField(
        max_length=20,
        choices=Network.choices,
        blank=True,
        null=True,
    )
    card_type = models.CharField(
        max_length=20,
        choices=CardType.choices,
        blank=True,
        null=True,
    )
    product_family = models.SlugField(max_length=255, blank=True, null=True)
    recommended_credit_profile = models.CharField(
        max_length=20,
        choices=CreditProfile.choices,
        blank=True,
        null=True,
    )
    annual_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    annual_fee_waived_first_year = models.BooleanField(blank=True, null=True)
    foreign_transaction_fee = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
    )
    credit_score_min = models.PositiveSmallIntegerField(blank=True, null=True)
    reward_currency = models.CharField(max_length=255, blank=True, null=True)
    reward_currency_name = models.CharField(max_length=255, blank=True, null=True)
    application_rules = models.TextField(blank=True, null=True)
    is_discontinued = models.BooleanField(default=False)
    product_url = models.URLField(blank=True, null=True)
    official_page_verified_at = models.DateField(blank=True, null=True)
    official_page_updated_at = models.DateField(blank=True, null=True)
    cardapi_updated_at = models.DateTimeField(blank=True, null=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    curated_sources = models.JSONField(blank=True, default=dict)

    def __str__(self):
        return f"{self.name} - {self.issuer.name} - {self.network or 'Unknown network'}"


class RewardProgram(TimestampedModel):
    class Unit(models.TextChoices):
        POINTS = "points", "Points"
        MILES = "miles", "Miles"
        CASH = "cash", "Cash back"

    class ProgramType(models.TextChoices):
        ISSUER = "issuer", "Issuer rewards"
        AIRLINE = "airline", "Airline loyalty"
        HOTEL = "hotel", "Hotel loyalty"
        CASH = "cash", "Cash back"

    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    issuer = models.ForeignKey(
        Issuer, related_name="reward_programs", on_delete=models.PROTECT,
        blank=True, null=True,
    )
    unit = models.CharField(max_length=20, choices=Unit.choices)
    program_type = models.CharField(
        max_length=20,
        choices=ProgramType.choices,
        default=ProgramType.ISSUER,
    )
    cash_value_cpp = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    travel_portal_cpp = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    transfer_value_cpp = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    verified_at = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class CardRewardProgram(TimestampedModel):
    credit_card = models.ForeignKey(CreditCard, related_name="reward_program_memberships", on_delete=models.CASCADE)
    reward_program = models.ForeignKey(RewardProgram, related_name="card_memberships", on_delete=models.PROTECT)
    is_primary = models.BooleanField(default=True)
    can_cash_redeem = models.BooleanField(default=False)
    can_use_travel_portal = models.BooleanField(default=False)
    can_transfer_partners = models.BooleanField(default=False)
    can_combine_rewards = models.BooleanField(default=False)
    source_url = models.URLField(blank=True, null=True)
    verified_at = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("credit_card", "reward_program"), name="unique_card_reward_program")]

    def __str__(self):
        return f"{self.credit_card.name} - {self.reward_program.name}"


class RewardProgramUnlock(TimestampedModel):
    class Capability(models.TextChoices):
        TRANSFER_PARTNERS = "transfer_partners", "Transfer partners"
        TRAVEL_PORTAL = "travel_portal", "Travel portal"

    reward_program = models.ForeignKey(RewardProgram, related_name="unlock_rules", on_delete=models.CASCADE)
    source_card = models.ForeignKey(CreditCard, related_name="reward_unlock_sources", on_delete=models.CASCADE)
    required_card = models.ForeignKey(CreditCard, related_name="reward_unlock_requirements", on_delete=models.CASCADE)
    capability = models.CharField(max_length=32, choices=Capability.choices)
    conversion_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    source_url = models.URLField()
    verified_at = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("reward_program", "source_card", "required_card", "capability"), name="unique_reward_program_unlock")]

    def __str__(self):
        return f"{self.source_card.name} + {self.required_card.name}: {self.capability}"


class RewardTransferRoute(TimestampedModel):
    source_key = models.CharField(max_length=255, unique=True)
    source_program = models.ForeignKey(
        RewardProgram,
        related_name="outgoing_transfer_routes",
        on_delete=models.CASCADE,
    )
    destination_program = models.ForeignKey(
        RewardProgram,
        related_name="incoming_transfer_routes",
        on_delete=models.PROTECT,
    )
    eligible_card = models.ForeignKey(
        CreditCard,
        related_name="transfer_route_rules",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Optional card-specific override for this transfer route.",
    )
    source_amount = models.DecimalField(
        max_digits=14, decimal_places=4, blank=True, null=True
    )
    destination_amount = models.DecimalField(
        max_digits=14, decimal_places=4, blank=True, null=True
    )
    minimum_transfer = models.PositiveIntegerField(blank=True, null=True)
    transfer_increment = models.PositiveIntegerField(blank=True, null=True)
    effective_from = models.DateField(blank=True, null=True)
    effective_through = models.DateField(blank=True, null=True)
    account_opened_before = models.DateField(blank=True, null=True)
    account_opened_on_or_after = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    source_url = models.URLField()
    verified_at = models.DateField()
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(source_program=models.F("destination_program")),
                name="transfer_route_programs_differ",
            ),
        ]

    def __str__(self):
        return f"{self.source_program.name} → {self.destination_program.name}"


class CCRewardRate(TimestampedModel):
    class RateType(models.TextChoices):
        MULTIPLIER = "multiplier", "Multiplier"
        PERCENT_CASHBACK = "percent_cashback", "Percent cashback"
        POINTS_PER_DOLLAR = "points_per_dollar", "Points per dollar"

    class CapPeriod(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        ANNUAL = "annual", "Annual"

    class BookingChannel(models.TextChoices):
        DIRECT = "direct", "Direct"
        ISSUER_PORTAL = "issuer_portal", "Issuer portal"
        OTHER_PORTAL = "other_portal", "Other portal"

    class TransactionMethod(models.TextChoices):
        ONLINE = "online", "Online"
        IN_STORE = "in_store", "In store"

    cardapi_id = models.UUIDField(blank=True, null=True, unique=True)
    credit_card = models.ForeignKey(
        CreditCard,
        related_name="reward_rates",
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        RewardCategory,
        related_name="reward_rates",
        on_delete=models.PROTECT,
    )
    rate_multiplier = models.DecimalField(max_digits=10, decimal_places=4)
    rate_type = models.CharField(max_length=32, choices=RateType.choices)
    cap_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    cap_period = models.CharField(
        max_length=32,
        choices=CapPeriod.choices,
        blank=True,
        null=True,
    )
    fallback_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        blank=True,
        null=True,
    )
    is_base_rate = models.BooleanField(default=False)
    is_rotating = models.BooleanField(default=False)
    rotating_quarter = models.PositiveSmallIntegerField(blank=True, null=True)
    rotating_year = models.PositiveSmallIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    booking_channel = models.CharField(
        max_length=32,
        choices=BookingChannel.choices,
        blank=True,
        null=True,
    )
    booking_portal = models.CharField(max_length=255, blank=True, null=True)
    geographic_scope = models.CharField(max_length=255, blank=True, null=True)
    transaction_method = models.CharField(
        max_length=20,
        choices=TransactionMethod.choices,
        blank=True,
        null=True,
    )
    merchant_scope = models.TextField(blank=True, null=True)
    enrollment_required = models.BooleanField(blank=True, null=True)
    minimum_transaction = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    valid_from = models.DateField(blank=True, null=True)
    expires_on = models.DateField(blank=True, null=True)
    cardapi_created_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    source_key = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    verified_at = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("credit_card", "source_key"),
                name="unique_card_reward_source_key",
            ),
        ]

    def __str__(self):
        return (
            f"{self.credit_card.name} - {self.category.category} "
            f"{self.rate_multiplier} {self.rate_type}"
        )


class SignupBonus(TimestampedModel):
    class SourceType(models.TextChoices):
        CARDAPI = "cardapi", "CardAPI"
        CURATED = "curated", "Curated"

    credit_card = models.ForeignKey(
        CreditCard,
        related_name="signup_bonuses",
        on_delete=models.CASCADE,
    )
    offer_text = models.TextField()
    bonus_amount = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        blank=True,
        null=True,
    )
    bonus_unit = models.CharField(
        max_length=20,
        choices=RewardProgram.Unit.choices,
        blank=True,
        null=True,
    )
    reward_program = models.ForeignKey(
        RewardProgram,
        related_name="signup_bonuses",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    minimum_spend = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    minimum_spend_months = models.PositiveSmallIntegerField(blank=True, null=True)
    source_key = models.CharField(max_length=64)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    source_url = models.URLField(blank=True, null=True)
    verified_at = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    first_seen_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("credit_card", "source_type", "source_key"),
                name="unique_card_signup_bonus_source",
            ),
        ]

    def __str__(self):
        return f"{self.credit_card.name} - {self.offer_text[:80]}"


class StatementCredit(TimestampedModel):
    class Period(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        SEMI_ANNUAL = "semi_annual", "Semiannual"
        ANNUAL = "annual", "Annual"

    cardapi_id = models.UUIDField(blank=True, null=True, unique=True)
    credit_card = models.ForeignKey(
        CreditCard,
        related_name="statement_credits",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    period = models.CharField(
        max_length=32,
        choices=Period.choices,
        blank=True,
        null=True,
    )
    eligible_merchants = models.TextField(blank=True, null=True)
    enrollment_required = models.BooleanField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    source_key = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    verified_at = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("credit_card", "source_key"),
                name="unique_card_credit_source_key",
            ),
        ]

    def __str__(self):
        return f"{self.credit_card.name} - {self.name}"


class Perk(TimestampedModel):
    class CoverageType(models.TextChoices):
        PRIMARY = "primary", "Primary"
        SECONDARY = "secondary", "Secondary"

    cardapi_id = models.UUIDField(blank=True, null=True, unique=True)
    credit_card = models.ForeignKey(
        CreditCard,
        related_name="perks",
        on_delete=models.CASCADE,
    )
    perk_type = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    period = models.CharField(max_length=255, blank=True, null=True)
    partner = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    enrollment_required = models.BooleanField(blank=True, null=True)
    spend_requirement = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    expires_on = models.DateField(blank=True, null=True)
    geographic_scope = models.CharField(max_length=255, blank=True, null=True)
    is_complimentary = models.BooleanField(blank=True, null=True)
    coverage_type = models.CharField(
        max_length=20,
        choices=CoverageType.choices,
        blank=True,
        null=True,
    )
    benefit_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
    )
    recommendation_notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(blank=True, null=True)
    source_key = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    verified_at = models.DateField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("credit_card", "source_key"),
                name="unique_card_perk_source_key",
            ),
        ]

    def __str__(self):
        return f"{self.credit_card.name} - {self.name}"
