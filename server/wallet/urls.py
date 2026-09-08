from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BudgetCategoryViewSet,
    CreditUseViewSet,
    MonthlyIncomeView,
    OwnedCardViewSet,
    SpendLogEntryViewSet,
)

router = DefaultRouter()
router.register("cards", OwnedCardViewSet, basename="owned-card")
router.register("credit-uses", CreditUseViewSet, basename="credit-use")
router.register("budget-categories", BudgetCategoryViewSet, basename="budget-category")
router.register("spend-log", SpendLogEntryViewSet, basename="spend-log-entry")

urlpatterns = [
    path("income/", MonthlyIncomeView.as_view(), name="monthly-income"),
    path("", include(router.urls)),
]
