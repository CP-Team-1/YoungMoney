from django.urls import path

from cardapi.views import (
    CandidateAnalysisView,
    CreditCardDetailView,
    CreditCardListView,
    CardComparisonView,
    IssuerListView,
    PortfolioEvaluationView,
    PortfolioRecommendationView,
    RewardCategoryListView,
    RewardGoalMatchView,
    RewardProgramListView,
)


app_name = "cardapi"

urlpatterns = [
    path("cards/", CreditCardListView.as_view(), name="card-list"),
    path("cards/compare/", CardComparisonView.as_view(), name="card-compare"),
    path("cards/<slug:slug>/", CreditCardDetailView.as_view(), name="card-detail"),
    path(
        "portfolio/evaluate/",
        PortfolioEvaluationView.as_view(),
        name="portfolio-evaluate",
    ),
    path(
        "portfolio/analyze-candidates/",
        CandidateAnalysisView.as_view(),
        name="portfolio-analyze-candidates",
    ),
    path(
        "portfolio/recommend/",
        PortfolioRecommendationView.as_view(),
        name="portfolio-recommend",
    ),
    path("issuers/", IssuerListView.as_view(), name="issuer-list"),
    path(
        "reward-categories/",
        RewardCategoryListView.as_view(),
        name="reward-category-list",
    ),
    path(
        "reward-programs/",
        RewardProgramListView.as_view(),
        name="reward-program-list",
    ),
    path(
        "reward-goals/match/",
        RewardGoalMatchView.as_view(),
        name="reward-goal-match",
    ),
]
