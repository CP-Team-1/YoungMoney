from django.db import migrations, models


def populate_local_slugs(apps, schema_editor):
    CreditCard = apps.get_model("cardapi", "CreditCard")
    for card in CreditCard.objects.all().iterator():
        card.local_slug = card.cardapi_slug
        card.save(update_fields=["local_slug"])


class Migration(migrations.Migration):
    dependencies = [
        ("cardapi", "0003_creditcard_product_provenance"),
    ]

    operations = [
        migrations.AddField(
            model_name="creditcard",
            name="local_slug",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="creditcard",
            name="product_family",
            field=models.SlugField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="creditcard",
            name="recommended_credit_profile",
            field=models.CharField(
                blank=True,
                choices=[
                    ("excellent", "Excellent"),
                    ("good", "Good"),
                    ("fair", "Fair"),
                    ("student", "Student"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.RunPython(populate_local_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="creditcard",
            name="local_slug",
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="creditcard",
            name="cardapi_slug",
            field=models.SlugField(
                blank=True,
                max_length=255,
                null=True,
                unique=True,
            ),
        ),
    ]
