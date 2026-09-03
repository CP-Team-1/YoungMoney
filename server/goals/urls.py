from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GoalTypeListView, UserGoalViewSet

router = DefaultRouter()
router.register("", UserGoalViewSet, basename="user-goal")

urlpatterns = [
    path("types/", GoalTypeListView.as_view(), name="goal-type-list"),
    path("", include(router.urls)),
]
