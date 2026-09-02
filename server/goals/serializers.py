from rest_framework import serializers

from .models import Goal, UserGoal


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ["id", "goal"]


class UserGoalSerializer(serializers.ModelSerializer):
    goal_name = serializers.CharField(source="goal.goal", read_only=True)

    class Meta:
        model = UserGoal
        fields = ["id", "goal", "goal_name", "name", "target", "notes"]
        read_only_fields = ["id", "goal_name"]
        extra_kwargs = {"notes": {"required": False, "allow_blank": True}}

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Goal name cannot be blank.")
        return value
