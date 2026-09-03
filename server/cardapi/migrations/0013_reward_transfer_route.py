import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cardapi", "0012_reward_program_type")]

    operations = [
        migrations.CreateModel(
            name="RewardTransferRoute",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                ("source_key", models.CharField(max_length=255, unique=True)),
                ("source_amount", models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True)),
                ("destination_amount", models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True)),
                ("minimum_transfer", models.PositiveIntegerField(blank=True, null=True)),
                ("transfer_increment", models.PositiveIntegerField(blank=True, null=True)),
                ("effective_from", models.DateField(blank=True, null=True)),
                ("effective_through", models.DateField(blank=True, null=True)),
                ("account_opened_before", models.DateField(blank=True, null=True)),
                ("account_opened_on_or_after", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True, null=True)),
                ("source_url", models.URLField()),
                ("verified_at", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("destination_program", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="incoming_transfer_routes", to="cardapi.rewardprogram")),
                ("eligible_card", models.ForeignKey(blank=True, help_text="Optional card-specific override for this transfer route.", null=True, on_delete=django.db.models.deletion.CASCADE, related_name="transfer_route_rules", to="cardapi.creditcard")),
                ("source_program", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_transfer_routes", to="cardapi.rewardprogram")),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=~models.Q(source_program=models.F("destination_program")),
                        name="transfer_route_programs_differ",
                    )
                ]
            },
        )
    ]
