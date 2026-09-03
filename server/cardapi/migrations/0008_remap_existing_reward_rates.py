from django.db import migrations


def remap_rates(apps, schema_editor):
    CCRewardRate = apps.get_model("cardapi", "CCRewardRate")
    RewardCategory = apps.get_model("cardapi", "RewardCategory")

    mappings = {
        "airline": "flights",
        "rental_cars": "car_rentals",
        "everything": "other",
        "amazon": "online_shopping",
        "chase_travel": "travel",
        "allegiant_travel": "travel",
        "air_travel_and_other_hotels": "travel",
        "travel_portal": "travel",
        "travel_portal_flights": "travel",
        "travel_portal_hotels_cars": "travel",
        "travel_portal_hotels_cars_attractions": "travel",
        "online_grocery": "groceries",
    }
    for source_slug, target_slug in mappings.items():
        target = RewardCategory.objects.get(slug=target_slug)
        CCRewardRate.objects.filter(category__slug=source_slug).update(
            category_id=target.pk
        )


class Migration(migrations.Migration):
    dependencies = [
        ("cardapi", "0007_normalize_reward_category_aliases"),
    ]

    operations = [
        migrations.RunPython(remap_rates, migrations.RunPython.noop),
    ]
