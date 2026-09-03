from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cardapi", "0004_creditcard_local_identity"),
    ]

    operations = [
        migrations.AddField(model_name="perk", name="enrollment_required", field=models.BooleanField(blank=True, null=True)),
        migrations.AddField(model_name="perk", name="spend_requirement", field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
        migrations.AddField(model_name="perk", name="expires_on", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="perk", name="geographic_scope", field=models.CharField(blank=True, max_length=255, null=True)),
        migrations.AddField(model_name="perk", name="is_complimentary", field=models.BooleanField(blank=True, null=True)),
        migrations.AddField(model_name="perk", name="coverage_type", field=models.CharField(blank=True, choices=[("primary", "Primary"), ("secondary", "Secondary")], max_length=20, null=True)),
        migrations.AddField(model_name="perk", name="benefit_limit", field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
        migrations.AddField(model_name="perk", name="recommendation_notes", field=models.TextField(blank=True, null=True)),
    ]
