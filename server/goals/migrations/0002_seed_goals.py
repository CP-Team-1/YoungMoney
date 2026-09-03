from django.db import migrations


GOAL_TYPES = ("Debt free", "Purchase", "Savings")


def seed_goal_types(apps, schema_editor):
    Goal = apps.get_model("goals", "Goal")
    for goal_type in GOAL_TYPES:
        Goal.objects.get_or_create(goal=goal_type)


def remove_goal_types(apps, schema_editor):
    Goal = apps.get_model("goals", "Goal")
    Goal.objects.filter(goal__in=GOAL_TYPES, user_goals__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("goals", "0001_initial")]

    operations = [migrations.RunPython(seed_goal_types, remove_goal_types)]
