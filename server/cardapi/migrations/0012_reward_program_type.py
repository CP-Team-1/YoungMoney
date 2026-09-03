from django.db import migrations, models


def classify_cash_programs(apps, schema_editor):
    RewardProgram = apps.get_model("cardapi", "RewardProgram")
    RewardProgram.objects.filter(unit="cash").update(program_type="cash")


class Migration(migrations.Migration):
    dependencies = [("cardapi", "0011_correct_signup_bonus_units")]

    operations = [
        migrations.AddField(
            model_name="rewardprogram",
            name="program_type",
            field=models.CharField(
                choices=[
                    ("issuer", "Issuer rewards"),
                    ("airline", "Airline loyalty"),
                    ("hotel", "Hotel loyalty"),
                    ("cash", "Cash back"),
                ],
                default="issuer",
                max_length=20,
            ),
        ),
        migrations.RunPython(classify_cash_programs, migrations.RunPython.noop),
    ]
