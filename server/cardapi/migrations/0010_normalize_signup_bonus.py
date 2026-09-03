import django.db.models.deletion
from django.db import migrations, models


def populate_bonus_units_and_programs(apps, schema_editor):
    SignupBonus = apps.get_model("cardapi", "SignupBonus")
    CardRewardProgram = apps.get_model("cardapi", "CardRewardProgram")

    for bonus in SignupBonus.objects.all().iterator():
        offer = (bonus.offer_text or "").casefold()
        if "mile" in offer:
            unit = "miles"
        elif "point" in offer:
            unit = "points"
        elif "$" in offer or "cash" in offer or "statement credit" in offer:
            unit = "cash"
        else:
            unit = None

        membership = (
            CardRewardProgram.objects.filter(
                credit_card_id=bonus.credit_card_id,
                is_active=True,
                is_primary=True,
            )
            .select_related("reward_program")
            .first()
        )
        if unit is None and membership:
            unit = membership.reward_program.unit

        bonus.bonus_unit = unit
        if membership and unit == membership.reward_program.unit:
            bonus.reward_program_id = membership.reward_program_id
        bonus.save(update_fields=("bonus_unit", "reward_program"))


class Migration(migrations.Migration):
    dependencies = [("cardapi", "0009_rewardprogram_cardrewardprogram_rewardprogramunlock")]

    operations = [
        migrations.RenameField(
            model_name="signupbonus",
            old_name="reported_value",
            new_name="bonus_amount",
        ),
        migrations.AddField(
            model_name="signupbonus",
            name="bonus_unit",
            field=models.CharField(
                blank=True,
                choices=[
                    ("points", "Points"),
                    ("miles", "Miles"),
                    ("cash", "Cash back"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="signupbonus",
            name="reward_program",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="signup_bonuses",
                to="cardapi.rewardprogram",
            ),
        ),
        migrations.RunPython(populate_bonus_units_and_programs, migrations.RunPython.noop),
    ]
