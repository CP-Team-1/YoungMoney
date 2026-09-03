from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cardapi", "0002_card_owned_credits_and_perks"),
    ]

    operations = [
        migrations.AddField(
            model_name="creditcard",
            name="product_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="creditcard",
            name="official_page_verified_at",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="creditcard",
            name="official_page_updated_at",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="creditcard",
            name="cardapi_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
