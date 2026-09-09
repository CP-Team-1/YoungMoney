from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArticleReadView,
    BudgetCategoryViewSet,
    CreditUseViewSet,
    DailyTaskViewSet,
    MonthlyIncomeView,
    OwnedCardViewSet,
    SpendLogEntryViewSet,
)

router = DefaultRouter()
router.register("cards", OwnedCardViewSet, basename="owned-card")
router.register("credit-uses", CreditUseViewSet, basename="credit-use")
router.register("budget-categories", BudgetCategoryViewSet, basename="budget-category")
router.register("spend-log", SpendLogEntryViewSet, basename="spend-log-entry")
router.register("daily-tasks", DailyTaskViewSet, basename="daily-task")

urlpatterns = [
    path("income/", MonthlyIncomeView.as_view(), name="monthly-income"),
    path("article-reads/", ArticleReadView.as_view(), name="article-reads"),
    path("", include(router.urls)),
]
