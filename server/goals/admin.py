from django.contrib import admin

from .models import Goal, UserGoal


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("id", "goal")
    search_fields = ("goal",)


@admin.register(UserGoal)
class UserGoalAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "goal", "target")
    list_filter = ("goal",)
    search_fields = ("name", "user__email", "notes")
