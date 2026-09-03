import django.db.models.deletion
from django.db import migrations, models


def migrate_legacy_rows(apps, schema_editor):
    LegacyIncentive = apps.get_model("cardapi", "LegacyIncentive")
    LegacyPerk = apps.get_model("cardapi", "LegacyPerk")
    CCIncentive = apps.get_model("cardapi", "CCIncentive")
    CCPerk = apps.get_model("cardapi", "CCPerk")
    StatementCredit = apps.get_model("cardapi", "StatementCredit")
    Perk = apps.get_model("cardapi", "Perk")

    incentives = {row.pk: row for row in LegacyIncentive.objects.all()}
    for link in CCIncentive.objects.all():
        legacy = incentives[link.incentive_id]
        StatementCredit.objects.create(
            credit_card_id=link.credit_card_id,
            name=legacy.incentive,
            amount=legacy.value,
            period=legacy.frequency,
            notes=legacy.description,
            source_key=f"legacy-cc-incentive-{link.pk}",
        )

    perks = {row.pk: row for row in LegacyPerk.objects.all()}
    for link in CCPerk.objects.all():
        legacy = perks[link.perk_id]
        Perk.objects.create(
            credit_card_id=link.credit_card_id,
            name=legacy.perk,
            value=legacy.value,
            period=legacy.frequency,
            details=legacy.description,
            source_key=f"legacy-cc-perk-{link.pk}",
        )


class Migration(migrations.Migration):
    dependencies = [
        ("cardapi", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Incentive",
            new_name="LegacyIncentive",
        ),
        migrations.RenameModel(
            old_name="Perk",
            new_name="LegacyPerk",
        ),
        migrations.CreateModel(
            name="StatementCredit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                (
                    "cardapi_id",
                    models.UUIDField(blank=True, null=True, unique=True),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=14,
                        null=True,
                    ),
                ),
                (
                    "period",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("monthly", "Monthly"),
                            ("quarterly", "Quarterly"),
                            ("semi_annual", "Semiannual"),
                            ("annual", "Annual"),
                        ],
                        max_length=32,
                        null=True,
                    ),
                ),
                ("eligible_merchants", models.TextField(blank=True, null=True)),
                (
                    "enrollment_required",
                    models.BooleanField(blank=True, null=True),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                (
                    "source_key",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("source_url", models.URLField(blank=True, null=True)),
                ("verified_at", models.DateField(blank=True, null=True)),
                (
                    "credit_card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="statement_credits",
                        to="cardapi.creditcard",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("credit_card", "source_key"),
                        name="unique_card_credit_source_key",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Perk",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                (
                    "cardapi_id",
                    models.UUIDField(blank=True, null=True, unique=True),
                ),
                ("perk_type", models.CharField(blank=True, max_length=255, null=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "value",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=14,
                        null=True,
                    ),
                ),
                ("period", models.CharField(blank=True, max_length=255, null=True)),
                ("partner", models.CharField(blank=True, max_length=255, null=True)),
                ("details", models.TextField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                (
                    "source_key",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("source_url", models.URLField(blank=True, null=True)),
                ("verified_at", models.DateField(blank=True, null=True)),
                (
                    "credit_card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perks",
                        to="cardapi.creditcard",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("credit_card", "source_key"),
                        name="unique_card_perk_source_key",
                    )
                ],
            },
        ),
        migrations.RunPython(migrate_legacy_rows, migrations.RunPython.noop),
        migrations.DeleteModel(name="CCIncentive"),
        migrations.DeleteModel(name="CCPerk"),
        migrations.DeleteModel(name="LegacyIncentive"),
        migrations.DeleteModel(name="LegacyPerk"),
    ]
