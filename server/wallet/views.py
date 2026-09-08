from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from cardapi.models import CreditCard

from .models import BudgetCategory, MonthlyIncome, OwnedCard, OwnedCardCreditUse, SpendLogEntry
from .serializers import (
    BudgetCategoryCreateSerializer,
    BudgetCategorySerializer,
    BudgetCategoryUpdateSerializer,
    CreditUseCreateSerializer,
    MonthlyIncomeSerializer,
    OwnedCardCreateSerializer,
    OwnedCardSerializer,
    SpendLogEntrySerializer,
)


class OwnedCardViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "card__local_slug"
    lookup_url_kwarg = "card_slug"

    def get_queryset(self):
        return OwnedCard.objects.filter(user=self.request.user).select_related("card", "card__issuer")

    def get_serializer_class(self):
        if self.action == "create":
            return OwnedCardCreateSerializer
        return OwnedCardSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        card = CreditCard.objects.get(local_slug=serializer.validated_data["card_slug"])
        owned, created = OwnedCard.objects.get_or_create(user=request.user, card=card)
        if created:
            OwnedCardCreditUse.objects.bulk_create(
                OwnedCardCreditUse(owned_card=owned, statement_credit=credit)
                for credit in card.statement_credits.filter(is_active=True)
            )
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(OwnedCardSerializer(owned).data, status=response_status)


class CreditUseViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CreditUseCreateSerializer
    lookup_field = "statement_credit_id"
    lookup_url_kwarg = "statement_credit_id"

    def get_queryset(self):
        return OwnedCardCreditUse.objects.filter(owned_card__user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        OwnedCardCreditUse.objects.get_or_create(
            owned_card=serializer.validated_data["owned_card"],
            statement_credit=serializer.validated_data["statement_credit"],
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        self.get_queryset().filter(statement_credit_id=kwargs["statement_credit_id"]).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MonthlyIncomeView(APIView):
    def get(self, request):
        income, _ = MonthlyIncome.objects.get_or_create(user=request.user)
        return Response(MonthlyIncomeSerializer(income).data)

    def put(self, request):
        income, _ = MonthlyIncome.objects.get_or_create(user=request.user)
        serializer = MonthlyIncomeSerializer(income, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class BudgetCategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    lookup_field = "key"
    lookup_url_kwarg = "key"

    def get_queryset(self):
        return BudgetCategory.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return BudgetCategoryCreateSerializer
        if self.action in ("update", "partial_update"):
            return BudgetCategoryUpdateSerializer
        return BudgetCategorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = BudgetCategory.objects.create(
            user=request.user,
            key=serializer.validated_data["key"],
            label=serializer.validated_data["label"],
            allocated=serializer.validated_data["allocated"],
            color=serializer.validated_data["color"],
        )
        return Response(BudgetCategorySerializer(category).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        category = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(category, field, value)
        category.save()
        return Response(BudgetCategorySerializer(category).data)


class SpendLogEntryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = SpendLogEntrySerializer

    def get_queryset(self):
        return SpendLogEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["delete"])
    def clear(self, request):
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
