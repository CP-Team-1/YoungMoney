from rest_framework import generics, viewsets

from .models import Goal, UserGoal
from .serializers import GoalSerializer, UserGoalSerializer


class GoalTypeListView(generics.ListAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer


class UserGoalViewSet(viewsets.ModelViewSet):
    serializer_class = UserGoalSerializer

    def get_queryset(self):
        return UserGoal.objects.filter(user=self.request.user).select_related("goal")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
