from decimal import Decimal

from rest_framework import serializers

from .models import Goal, UserGoal


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            "id",
            "goal",
        ]


class UserGoalSerializer(serializers.ModelSerializer):
    goal_name = serializers.SerializerMethodField()

    class Meta:
        model = UserGoal

        fields = [
            "id",
            "goal",
            "goal_name",
            "custom_goal_type",
            "name",
            "target",
            "current",
            "notes",
        ]

        read_only_fields = [
            "id",
            "goal_name",
        ]

        extra_kwargs = {
            "goal": {
                "required": False,
                "allow_null": True,
            },
            "custom_goal_type": {
                "required": False,
                "allow_blank": True,
            },
            "notes": {
                "required": False,
                "allow_blank": True,
            },
            "current": {
                "required": False,
            },
        }

    def get_goal_name(self, obj):
        if obj.goal:
            return obj.goal.goal

        return obj.custom_goal_type

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Goal name cannot be blank."
            )

        return value

    def validate_custom_goal_type(self, value):
        return value.strip()

    def validate_current(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError(
                "Current amount cannot be negative."
            )

        return value

    def validate(self, attrs):
        instance = getattr(
            self,
            "instance",
            None,
        )

        if "goal" in attrs:
            goal = attrs["goal"]
        elif instance:
            goal = instance.goal
        else:
            goal = None

        if "custom_goal_type" in attrs:
            custom_goal_type = (
                attrs["custom_goal_type"].strip()
            )
        elif instance:
            custom_goal_type = (
                instance.custom_goal_type.strip()
            )
        else:
            custom_goal_type = ""

        if not goal and not custom_goal_type:
            raise serializers.ValidationError(
                {
                    "goal": (
                        "Choose a predefined goal "
                        "or provide a custom goal type."
                    )
                }
            )

        if goal and custom_goal_type:
            raise serializers.ValidationError(
                {
                    "custom_goal_type": (
                        "Use either a predefined goal "
                        "or a custom goal type, not both."
                    )
                }
            )

        return attrs