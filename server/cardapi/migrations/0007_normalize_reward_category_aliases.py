from django.db import migrations


def normalize_aliases(apps, schema_editor):
    RewardCategory = apps.get_model("cardapi", "RewardCategory")
    RewardCategoryAlias = apps.get_model("cardapi", "RewardCategoryAlias")

    canonical_slugs = {
        "other", "travel", "flights", "hotels", "car_rentals",
        "vacation_rentals", "cruises", "transit", "attractions",
        "dining", "groceries", "gas", "entertainment", "streaming",
        "drugstores", "phone_plans", "online_shopping",
    }
    RewardCategory.objects.exclude(slug__in=canonical_slugs).update(
        is_user_facing=False
    )

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
    for alias, category_slug in mappings.items():
        category = RewardCategory.objects.get(slug=category_slug)
        RewardCategoryAlias.objects.update_or_create(
            source="cardapi",
            alias=alias,
            defaults={"category": category},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("cardapi", "0006_reward_category_taxonomy_and_qualifiers"),
    ]

    operations = [
        migrations.RunPython(normalize_aliases, migrations.RunPython.noop),
    ]
