import django.db.models.deletion
from django.db import migrations, models


def seed_categories(apps, schema_editor):
    RewardCategory = apps.get_model("cardapi", "RewardCategory")
    RewardCategoryAlias = apps.get_model("cardapi", "RewardCategoryAlias")

    RewardCategory.objects.update(is_user_facing=False)
    definitions = [
        ("other", "Other", None),
        ("travel", "Travel", None),
        ("flights", "Flights", "travel"),
        ("hotels", "Hotels", "travel"),
        ("car_rentals", "Car Rentals", "travel"),
        ("vacation_rentals", "Vacation Rentals", "travel"),
        ("cruises", "Cruises", "travel"),
        ("transit", "Transit", "travel"),
        ("attractions", "Attractions", "travel"),
        ("dining", "Dining", None),
        ("groceries", "Groceries", None),
        ("gas", "Gas and EV Charging", None),
        ("entertainment", "Entertainment", None),
        ("streaming", "Streaming", "entertainment"),
        ("drugstores", "Drugstores", None),
        ("phone_plans", "Phone Plans", None),
        ("online_shopping", "Online Shopping", None),
    ]
    categories = {}
    for slug, name, _ in definitions:
        category, _ = RewardCategory.objects.get_or_create(
            slug=slug,
            defaults={"category": name},
        )
        category.category = name
        category.is_active = True
        category.is_user_facing = True
        category.save(update_fields=["category", "is_active", "is_user_facing"])
        categories[slug] = category

    for slug, _, parent_slug in definitions:
        category = categories[slug]
        category.parent = categories.get(parent_slug)
        category.save(update_fields=["parent"])
        RewardCategoryAlias.objects.get_or_create(
            source="cardapi",
            alias=slug,
            defaults={"category": category},
        )

    for legacy_slug in (
        "travel_portal",
        "travel_portal_hotels_cars",
        "travel_portal_flights",
        "online_grocery",
    ):
        RewardCategory.objects.filter(slug=legacy_slug).update(is_user_facing=False)


class Migration(migrations.Migration):
    dependencies = [
        ("cardapi", "0005_perk_recommendation_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="rewardcategory",
            name="parent",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="children", to="cardapi.rewardcategory"),
        ),
        migrations.AddField(model_name="rewardcategory", name="is_user_facing", field=models.BooleanField(default=True)),
        migrations.CreateModel(
            name="RewardCategoryAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("source", models.CharField(max_length=32)),
                ("alias", models.SlugField(max_length=255)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="aliases", to="cardapi.rewardcategory")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("source", "alias"), name="unique_reward_category_source_alias")]},
        ),
        migrations.AddField(model_name="ccrewardrate", name="booking_channel", field=models.CharField(blank=True, choices=[("direct", "Direct"), ("issuer_portal", "Issuer portal"), ("other_portal", "Other portal")], max_length=32, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="booking_portal", field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="geographic_scope", field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="transaction_method", field=models.CharField(blank=True, choices=[("online", "Online"), ("in_store", "In store")], max_length=20, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="merchant_scope", field=models.TextField(blank=True, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="enrollment_required", field=models.BooleanField(blank=True, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="minimum_transaction", field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="valid_from", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="ccrewardrate", name="expires_on", field=models.DateField(blank=True, null=True)),
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
