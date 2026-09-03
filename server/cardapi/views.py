from decimal import Decimal, InvalidOperation

from django.db.models import Count, Prefetch, Q
from rest_framework import generics, permissions, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from cardapi.models import (
    CreditCard,
    Issuer,
    RewardCategory,
    RewardProgram,
    SignupBonus,
    StatementCredit,
)
from cardapi.serializers import (
    CandidateAnalysisRequestSerializer,
    CandidateAnalysisResultSerializer,
    CreditCardDetailSerializer,
    CreditCardListSerializer,
    CardComparisonRequestSerializer,
    CardComparisonResultSerializer,
    IssuerCatalogSerializer,
    PortfolioEvaluationRequestSerializer,
    PortfolioEvaluationResultSerializer,
    PortfolioRecommendationRequestSerializer,
    PortfolioRecommendationResultSerializer,
    RewardCategoryCatalogSerializer,
    RewardProgramSummarySerializer,
    RewardGoalMatchRequestSerializer,
    CardGoalSummarySerializer,
    PortfolioGoalAggregateSerializer,
)
from cardapi.services.comparison import compare_cards
from cardapi.services.portfolio import (
    SignupBonusUse,
    SpendingBucket,
    StatementCreditUse,
    analyze_candidate_cards,
    evaluate_portfolio,
)
from cardapi.services.rewards import RewardMatchError
from cardapi.services.recommendations import recommend_portfolio
from cardapi.services.goals import (
    RewardGoal,
    RewardGoalError,
    match_reward_goals,
    summarize_portfolio_goals,
)


class CardCatalogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _boolean_parameter(value, name):
    normalized = str(value).strip().casefold()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise serializers.ValidationError({name: "Use true or false."})


class CreditCardListView(generics.ListAPIView):
    serializer_class = CreditCardListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = CardCatalogPagination

    def get_queryset(self):
        parameters = self.request.query_params
        queryset = CreditCard.objects.filter(issuer__is_active=True).select_related(
            "issuer"
        )

        include_discontinued = parameters.get("include_discontinued")
        if include_discontinued is None or not _boolean_parameter(
            include_discontinued, "include_discontinued"
        ):
            queryset = queryset.filter(is_discontinued=False)

        search = parameters.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(issuer__name__icontains=search)
                | Q(reward_currency_name__icontains=search)
            )

        issuer = parameters.get("issuer", "").strip()
        if issuer:
            queryset = queryset.filter(issuer__slug__iexact=issuer)

        card_type = parameters.get("card_type", "").strip()
        if card_type:
            valid_types = {value for value, _ in CreditCard.CardType.choices}
            if card_type not in valid_types:
                raise serializers.ValidationError(
                    {"card_type": f"Choose one of: {', '.join(sorted(valid_types))}."}
                )
            queryset = queryset.filter(card_type=card_type)

        maximum_fee = parameters.get("max_annual_fee")
        if maximum_fee is not None:
            try:
                maximum_fee = Decimal(maximum_fee)
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise serializers.ValidationError(
                    {"max_annual_fee": "Enter a valid non-negative amount."}
                ) from exc
            if not maximum_fee.is_finite() or maximum_fee < 0:
                raise serializers.ValidationError(
                    {"max_annual_fee": "Enter a valid non-negative amount."}
                )
            queryset = queryset.filter(annual_fee__lte=maximum_fee)

        category_slug = parameters.get("reward_category", "").strip()
        if category_slug:
            if not RewardCategory.objects.filter(
                slug=category_slug, is_active=True
            ).exists():
                raise serializers.ValidationError(
                    {"reward_category": "Unknown active reward category."}
                )
            queryset = queryset.filter(
                reward_rates__is_active=True,
                reward_rates__category__slug=category_slug,
            )

        return queryset.distinct().order_by("issuer__name", "name", "local_slug")


class CreditCardDetailView(generics.RetrieveAPIView):
    serializer_class = CreditCardDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "local_slug"
    lookup_url_kwarg = "slug"
    queryset = CreditCard.objects.filter(issuer__is_active=True).select_related("issuer")


class IssuerListView(generics.ListAPIView):
    serializer_class = IssuerCatalogSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            Issuer.objects.filter(is_active=True)
            .annotate(
                active_card_count=Count(
                    "credit_cards",
                    filter=Q(credit_cards__is_discontinued=False),
                    distinct=True,
                )
            )
            .filter(active_card_count__gt=0)
            .order_by("name", "slug")
        )


class RewardCategoryListView(generics.ListAPIView):
    serializer_class = RewardCategoryCatalogSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        children = RewardCategory.objects.filter(
            is_active=True,
            is_user_facing=True,
        ).select_related("parent").order_by("category", "slug")
        return (
            RewardCategory.objects.filter(
                is_active=True,
                is_user_facing=True,
                parent__isnull=True,
            )
            .prefetch_related(
                Prefetch("children", queryset=children, to_attr="catalog_children")
            )
            .order_by("category", "slug")
        )


class RewardProgramListView(generics.ListAPIView):
    serializer_class = RewardProgramSummarySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = RewardProgram.objects.filter(is_active=True)
        program_type = self.request.query_params.get("program_type", "").strip()
        if program_type:
            valid_types = {value for value, _ in RewardProgram.ProgramType.choices}
            if program_type not in valid_types:
                raise serializers.ValidationError(
                    {
                        "program_type": (
                            f"Choose one of: {', '.join(sorted(valid_types))}."
                        )
                    }
                )
            queryset = queryset.filter(program_type=program_type)
        return queryset.order_by("program_type", "name", "code")


class CardComparisonView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request_serializer = CardComparisonRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        cards_by_slug = CreditCard.objects.filter(
            local_slug__in=data["card_slugs"],
            issuer__is_active=True,
        ).in_bulk(field_name="local_slug")
        missing_cards = set(data["card_slugs"]) - set(cards_by_slug)
        if missing_cards:
            raise serializers.ValidationError(
                {"card_slugs": f"Unknown cards: {', '.join(sorted(missing_cards))}."}
            )

        owned_by_slug = CreditCard.objects.filter(
            local_slug__in=data["owned_card_slugs"],
            issuer__is_active=True,
        ).in_bulk(field_name="local_slug")
        missing_owned = set(data["owned_card_slugs"]) - set(owned_by_slug)
        if missing_owned:
            raise serializers.ValidationError(
                {
                    "owned_card_slugs": (
                        f"Unknown cards: {', '.join(sorted(missing_owned))}."
                    )
                }
            )

        try:
            category = RewardCategory.objects.get(
                slug=data["category_slug"],
                is_active=True,
                is_user_facing=True,
            )
        except RewardCategory.DoesNotExist as exc:
            raise serializers.ValidationError(
                {"category_slug": "Unknown active user-facing reward category."}
            ) from exc

        purchase_context = {
            name: data[name]
            for name in (
                "purchase_date",
                "booking_channel",
                "booking_portal",
                "geographic_scope",
                "transaction_method",
                "merchant_eligible",
                "enrolled",
                "category_spend_to_date",
            )
            if name in data
        }
        try:
            results = compare_cards(
                cards=[cards_by_slug[slug] for slug in data["card_slugs"]],
                owned_cards=[
                    owned_by_slug[slug] for slug in data["owned_card_slugs"]
                ],
                category=category,
                amount=data["amount"],
                valuation_strategy=data["valuation_strategy"],
                custom_cpp=data["custom_cpp"],
                **purchase_context,
            )
        except (RewardMatchError, ValueError) as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            {
                "category": RewardCategoryCatalogSerializer(category).data,
                "amount": data["amount"],
                "valuation_strategy": data["valuation_strategy"],
                "results": CardComparisonResultSerializer(results, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class PortfolioEvaluationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request_serializer = PortfolioEvaluationRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        cards_by_slug = CreditCard.objects.filter(
            local_slug__in=data["card_slugs"],
            issuer__is_active=True,
        ).in_bulk(field_name="local_slug")
        missing_cards = set(data["card_slugs"]) - set(cards_by_slug)
        if missing_cards:
            raise serializers.ValidationError(
                {"card_slugs": f"Unknown cards: {', '.join(sorted(missing_cards))}."}
            )
        cards = [cards_by_slug[slug] for slug in data["card_slugs"]]

        category_slugs = {item["category_slug"] for item in data["spending"]}
        categories_by_slug = RewardCategory.objects.filter(
            slug__in=category_slugs,
            is_active=True,
            is_user_facing=True,
        ).in_bulk(field_name="slug")
        missing_categories = category_slugs - set(categories_by_slug)
        if missing_categories:
            raise serializers.ValidationError(
                {
                    "spending": (
                        "Unknown active user-facing reward categories: "
                        f"{', '.join(sorted(missing_categories))}."
                    )
                }
            )

        context_fields = {
            "booking_channel",
            "booking_portal",
            "geographic_scope",
            "transaction_method",
            "merchant_eligible",
            "enrolled",
        }
        spending = [
            SpendingBucket(
                category=categories_by_slug[item["category_slug"]],
                annual_amount=item["annual_amount"],
                context={
                    name: item[name] for name in context_fields if name in item
                },
            )
            for item in data["spending"]
        ]

        credit_uses = []
        for item in data["statement_credit_uses"]:
            matches = list(
                StatementCredit.objects.filter(
                    credit_card__local_slug=item["card_slug"],
                    credit_card__issuer__is_active=True,
                    name=item["credit_name"],
                    is_active=True,
                ).select_related("credit_card")[:2]
            )
            if not matches:
                raise serializers.ValidationError(
                    {
                        "statement_credit_uses": (
                            f"Unknown active credit {item['credit_name']!r} for "
                            f"card {item['card_slug']!r}."
                        )
                    }
                )
            if len(matches) > 1:
                raise serializers.ValidationError(
                    {
                        "statement_credit_uses": (
                            f"Credit name {item['credit_name']!r} is ambiguous for "
                            f"card {item['card_slug']!r}."
                        )
                    }
                )
            credit_uses.append(
                StatementCreditUse(
                    statement_credit=matches[0],
                    utilization=item["utilization"],
                )
            )

        try:
            evaluation = evaluate_portfolio(
                cards=cards,
                spending=spending,
                valuation_strategy=data["valuation_strategy"],
                custom_cpp=data["custom_cpp"],
                statement_credit_uses=credit_uses,
            )
        except (RewardMatchError, TypeError, ValueError) as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            PortfolioEvaluationResultSerializer(evaluation).data,
            status=status.HTTP_200_OK,
        )


class CandidateAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request_serializer = CandidateAnalysisRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        current_by_slug = CreditCard.objects.filter(
            local_slug__in=data["current_card_slugs"],
            issuer__is_active=True,
        ).in_bulk(field_name="local_slug")
        missing_current = set(data["current_card_slugs"]) - set(current_by_slug)
        if missing_current:
            raise serializers.ValidationError(
                {
                    "current_card_slugs": (
                        f"Unknown cards: {', '.join(sorted(missing_current))}."
                    )
                }
            )

        candidates_by_slug = CreditCard.objects.filter(
            local_slug__in=data["candidate_card_slugs"],
            issuer__is_active=True,
            is_discontinued=False,
        ).in_bulk(field_name="local_slug")
        missing_candidates = set(data["candidate_card_slugs"]) - set(
            candidates_by_slug
        )
        if missing_candidates:
            raise serializers.ValidationError(
                {
                    "candidate_card_slugs": (
                        "Unknown or discontinued candidates: "
                        f"{', '.join(sorted(missing_candidates))}."
                    )
                }
            )

        category_slugs = {item["category_slug"] for item in data["spending"]}
        categories_by_slug = RewardCategory.objects.filter(
            slug__in=category_slugs,
            is_active=True,
            is_user_facing=True,
        ).in_bulk(field_name="slug")
        missing_categories = category_slugs - set(categories_by_slug)
        if missing_categories:
            raise serializers.ValidationError(
                {
                    "spending": (
                        "Unknown active user-facing reward categories: "
                        f"{', '.join(sorted(missing_categories))}."
                    )
                }
            )

        context_fields = {
            "booking_channel",
            "booking_portal",
            "geographic_scope",
            "transaction_method",
            "merchant_eligible",
            "enrolled",
        }
        spending = [
            SpendingBucket(
                category=categories_by_slug[item["category_slug"]],
                annual_amount=item["annual_amount"],
                context={
                    name: item[name] for name in context_fields if name in item
                },
            )
            for item in data["spending"]
        ]

        credit_uses = []
        for item in data["statement_credit_uses"]:
            matches = list(
                StatementCredit.objects.filter(
                    credit_card__local_slug=item["card_slug"],
                    credit_card__issuer__is_active=True,
                    name=item["credit_name"],
                    is_active=True,
                ).select_related("credit_card")[:2]
            )
            if not matches:
                raise serializers.ValidationError(
                    {
                        "statement_credit_uses": (
                            f"Unknown active credit {item['credit_name']!r} for "
                            f"card {item['card_slug']!r}."
                        )
                    }
                )
            if len(matches) > 1:
                raise serializers.ValidationError(
                    {
                        "statement_credit_uses": (
                            f"Credit name {item['credit_name']!r} is ambiguous for "
                            f"card {item['card_slug']!r}."
                        )
                    }
                )
            credit_uses.append(
                StatementCreditUse(
                    statement_credit=matches[0],
                    utilization=item["utilization"],
                )
            )

        bonus_uses = []
        for item in data["signup_bonus_uses"]:
            matches = list(
                SignupBonus.objects.filter(
                    credit_card__local_slug=item["card_slug"],
                    credit_card__issuer__is_active=True,
                    is_active=True,
                )
                .select_related("credit_card", "reward_program")
                .order_by("-last_seen_at", "-pk")[:2]
            )
            if not matches:
                raise serializers.ValidationError(
                    {
                        "signup_bonus_uses": (
                            f"Card {item['card_slug']!r} has no active signup bonus."
                        )
                    }
                )
            if len(matches) > 1:
                raise serializers.ValidationError(
                    {
                        "signup_bonus_uses": (
                            f"Card {item['card_slug']!r} has multiple active offers; "
                            "the catalog must resolve them before an offer can be included."
                        )
                    }
                )
            bonus_uses.append(
                SignupBonusUse(
                    signup_bonus=matches[0],
                    eligibility=item["eligibility"],
                    can_meet_minimum_spend=item["can_meet_minimum_spend"],
                )
            )

        try:
            analysis = analyze_candidate_cards(
                current_cards=[
                    current_by_slug[slug] for slug in data["current_card_slugs"]
                ],
                candidates=[
                    candidates_by_slug[slug]
                    for slug in data["candidate_card_slugs"]
                ],
                spending=spending,
                valuation_strategy=data["valuation_strategy"],
                custom_cpp=data["custom_cpp"],
                statement_credit_uses=credit_uses,
                signup_bonus_uses=bonus_uses,
            )
        except (RewardMatchError, TypeError, ValueError) as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        return Response(
            CandidateAnalysisResultSerializer(analysis).data,
            status=status.HTTP_200_OK,
        )


class RewardGoalMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request_serializer = RewardGoalMatchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        all_slugs = set(data["card_slugs"]) | set(data["owned_card_slugs"])
        cards_by_slug = CreditCard.objects.filter(
            local_slug__in=all_slugs,
            issuer__is_active=True,
        ).select_related("issuer").in_bulk(field_name="local_slug")
        missing_cards = sorted(all_slugs - set(cards_by_slug))
        if missing_cards:
            raise serializers.ValidationError(
                {"card_slugs": f"Unknown cards: {', '.join(missing_cards)}."}
            )

        program_codes = {
            code for goal in data["goals"] for code in goal["program_codes"]
        }
        programs_by_code = RewardProgram.objects.filter(
            code__in=program_codes,
            is_active=True,
        ).in_bulk(field_name="code")
        missing_programs = sorted(program_codes - set(programs_by_code))
        if missing_programs:
            raise serializers.ValidationError(
                {
                    "goals": (
                        "Unknown or inactive reward programs: "
                        f"{', '.join(missing_programs)}."
                    )
                }
            )

        cards = [cards_by_slug[slug] for slug in data["card_slugs"]]
        owned_cards = [cards_by_slug[slug] for slug in data["owned_card_slugs"]]
        goals = [
            RewardGoal(
                label=item["label"],
                programs=tuple(
                    programs_by_code[code] for code in item["program_codes"]
                ),
                priority=item["priority"],
            )
            for item in data["goals"]
        ]
        opened_dates = {
            cards_by_slug[slug].pk: opened_on
            for slug, opened_on in data["account_opened_dates"].items()
        }

        try:
            results = match_reward_goals(
                cards=cards,
                goals=goals,
                owned_cards=owned_cards,
                account_opened_dates=opened_dates,
                as_of=data["as_of"],
            )
            portfolio = summarize_portfolio_goals(
                cards=tuple(dict.fromkeys((*cards, *owned_cards))),
                goals=goals,
                account_opened_dates=opened_dates,
                as_of=data["as_of"],
            )
        except (RewardGoalError, TypeError, ValueError) as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        serializer_context = {
            "card_slugs_by_pk": {
                card.pk: card.local_slug for card in cards_by_slug.values()
            }
        }
        return Response(
            {
                "as_of": data["as_of"].isoformat(),
                "cards": CardGoalSummarySerializer(
                    results,
                    many=True,
                    context=serializer_context,
                ).data,
                "portfolio": PortfolioGoalAggregateSerializer(portfolio).data,
            },
            status=status.HTTP_200_OK,
        )


class PortfolioRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    max_evaluated_actions = 500

    _credit_profile_compatibility = {
        CreditCard.CreditProfile.EXCELLENT: {
            CreditCard.CreditProfile.EXCELLENT,
            CreditCard.CreditProfile.GOOD,
            CreditCard.CreditProfile.FAIR,
        },
        CreditCard.CreditProfile.GOOD: {
            CreditCard.CreditProfile.GOOD,
            CreditCard.CreditProfile.FAIR,
        },
        CreditCard.CreditProfile.FAIR: {CreditCard.CreditProfile.FAIR},
        CreditCard.CreditProfile.STUDENT: {CreditCard.CreditProfile.STUDENT},
    }

    def post(self, request):
        request_serializer = PortfolioRecommendationRequestSerializer(
            data=request.data
        )
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data

        current_by_slug = CreditCard.objects.filter(
            local_slug__in=data["current_card_slugs"],
            issuer__is_active=True,
        ).select_related("issuer").in_bulk(field_name="local_slug")
        missing_current = sorted(
            set(data["current_card_slugs"]) - set(current_by_slug)
        )
        if missing_current:
            raise serializers.ValidationError(
                {
                    "current_card_slugs": (
                        f"Unknown cards: {', '.join(missing_current)}."
                    )
                }
            )
        current_cards = [
            current_by_slug[slug] for slug in data["current_card_slugs"]
        ]

        category_slugs = {item["category_slug"] for item in data["spending"]}
        categories_by_slug = RewardCategory.objects.filter(
            slug__in=category_slugs,
            is_active=True,
            is_user_facing=True,
        ).in_bulk(field_name="slug")
        missing_categories = sorted(category_slugs - set(categories_by_slug))
        if missing_categories:
            raise serializers.ValidationError(
                {
                    "spending": (
                        "Unknown active user-facing reward categories: "
                        f"{', '.join(missing_categories)}."
                    )
                }
            )
        context_fields = {
            "booking_channel",
            "booking_portal",
            "geographic_scope",
            "transaction_method",
            "merchant_eligible",
            "enrolled",
        }
        spending = [
            SpendingBucket(
                category=categories_by_slug[item["category_slug"]],
                annual_amount=item["annual_amount"],
                context={
                    field: item[field]
                    for field in context_fields
                    if field in item
                },
            )
            for item in data["spending"]
        ]

        program_codes = {
            code for goal in data["goals"] for code in goal["program_codes"]
        }
        programs_by_code = RewardProgram.objects.filter(
            code__in=program_codes,
            is_active=True,
        ).in_bulk(field_name="code")
        missing_programs = sorted(program_codes - set(programs_by_code))
        if missing_programs:
            raise serializers.ValidationError(
                {
                    "goals": (
                        "Unknown or inactive reward programs: "
                        f"{', '.join(missing_programs)}."
                    )
                }
            )
        goals = [
            RewardGoal(
                label=item["label"],
                programs=tuple(
                    programs_by_code[code] for code in item["program_codes"]
                ),
                priority=item["priority"],
            )
            for item in data["goals"]
        ]

        candidate_queryset = CreditCard.objects.filter(
            issuer__is_active=True,
            issuer__country=data["country"],
            is_discontinued=False,
            card_type__in=data["allowed_card_types"],
        ).exclude(pk__in=[card.pk for card in current_cards])
        if data["excluded_card_slugs"]:
            candidate_queryset = candidate_queryset.exclude(
                local_slug__in=data["excluded_card_slugs"]
            )
        if data["issuer_slugs"]:
            active_issuer_slugs = set(
                Issuer.objects.filter(
                    slug__in=data["issuer_slugs"],
                    country=data["country"],
                    is_active=True,
                ).values_list("slug", flat=True)
            )
            missing_issuers = sorted(set(data["issuer_slugs"]) - active_issuer_slugs)
            if missing_issuers:
                raise serializers.ValidationError(
                    {
                        "issuer_slugs": (
                            "Unknown active issuers for the selected country: "
                            f"{', '.join(missing_issuers)}."
                        )
                    }
                )
            candidate_queryset = candidate_queryset.filter(
                issuer__slug__in=data["issuer_slugs"]
            )
        if data.get("credit_profile"):
            compatible = self._credit_profile_compatibility[data["credit_profile"]]
            candidate_queryset = candidate_queryset.filter(
                Q(recommended_credit_profile__in=compatible)
                | Q(recommended_credit_profile__isnull=True)
                | Q(recommended_credit_profile="")
            )
        candidates = list(candidate_queryset.select_related("issuer").order_by(
            "issuer__name", "name", "local_slug"
        ))
        evaluated_action_count = len(candidates) * (len(current_cards) + 1)
        if evaluated_action_count > self.max_evaluated_actions:
            raise serializers.ValidationError(
                {
                    "candidate_pool": (
                        f"This request would evaluate {evaluated_action_count} actions; "
                        f"the maximum is {self.max_evaluated_actions}. Narrow the pool "
                        "with issuer_slugs, allowed_card_types, credit_profile, or "
                        "excluded_card_slugs."
                    )
                }
            )

        credit_uses = []
        for item in data["statement_credit_uses"]:
            matches = list(
                StatementCredit.objects.filter(
                    credit_card__local_slug=item["card_slug"],
                    credit_card__issuer__is_active=True,
                    name=item["credit_name"],
                    is_active=True,
                ).select_related("credit_card")[:2]
            )
            if not matches:
                raise serializers.ValidationError(
                    {
                        "statement_credit_uses": (
                            f"Unknown active credit {item['credit_name']!r} for "
                            f"card {item['card_slug']!r}."
                        )
                    }
                )
            if len(matches) > 1:
                raise serializers.ValidationError(
                    {
                        "statement_credit_uses": (
                            f"Credit name {item['credit_name']!r} is ambiguous for "
                            f"card {item['card_slug']!r}."
                        )
                    }
                )
            credit_uses.append(
                StatementCreditUse(
                    statement_credit=matches[0],
                    utilization=item["utilization"],
                )
            )

        candidate_slugs = {card.local_slug for card in candidates}
        invalid_bonus_cards = sorted(
            {
                item["card_slug"]
                for item in data["signup_bonus_uses"]
                if item["card_slug"] not in candidate_slugs
            }
        )
        if invalid_bonus_cards:
            raise serializers.ValidationError(
                {
                    "signup_bonus_uses": (
                        "Bonus assumptions must belong to eligible candidates: "
                        f"{', '.join(invalid_bonus_cards)}."
                    )
                }
            )
        bonus_uses = []
        for item in data["signup_bonus_uses"]:
            matches = list(
                SignupBonus.objects.filter(
                    credit_card__local_slug=item["card_slug"],
                    is_active=True,
                )
                .select_related("credit_card", "reward_program")
                .order_by("-last_seen_at", "-pk")[:2]
            )
            if len(matches) != 1:
                message = (
                    f"Card {item['card_slug']!r} has no active signup bonus."
                    if not matches
                    else (
                        f"Card {item['card_slug']!r} has multiple active offers; "
                        "the catalog must resolve them before inclusion."
                    )
                )
                raise serializers.ValidationError({"signup_bonus_uses": message})
            bonus_uses.append(
                SignupBonusUse(
                    signup_bonus=matches[0],
                    eligibility=item["eligibility"],
                    can_meet_minimum_spend=item["can_meet_minimum_spend"],
                )
            )

        opened_dates = {
            current_by_slug[slug].pk: opened_on
            for slug, opened_on in data["account_opened_dates"].items()
        }
        try:
            recommendation = recommend_portfolio(
                current_cards=current_cards,
                candidates=candidates,
                spending=spending,
                annual_fee_budget=data["annual_fee_budget"],
                recommendation_priority=data["recommendation_priority"],
                valuation_strategy=data["valuation_strategy"],
                custom_cpp=data["custom_cpp"],
                statement_credit_uses=credit_uses,
                signup_bonus_uses=bonus_uses,
                reward_goals=goals,
                account_opened_dates=opened_dates,
                as_of=data["as_of"],
                result_limit=data["result_limit"],
            )
        except (RewardGoalError, RewardMatchError, TypeError, ValueError) as exc:
            raise serializers.ValidationError({"detail": str(exc)}) from exc

        serializer_context = {
            "card_slugs_by_pk": {
                card.pk: card.local_slug for card in (*current_cards, *candidates)
            }
        }
        return Response(
            PortfolioRecommendationResultSerializer(
                recommendation,
                context=serializer_context,
            ).data,
            status=status.HTTP_200_OK,
        )
