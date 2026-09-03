from django.db import migrations


def correct_bonus_units(apps, schema_editor):
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
            unit = bonus.bonus_unit

        membership = (
            CardRewardProgram.objects.filter(
                credit_card_id=bonus.credit_card_id,
                is_active=True,
                is_primary=True,
                reward_program__unit=unit,
            )
            .select_related("reward_program")
            .first()
        )
        bonus.bonus_unit = unit
        bonus.reward_program_id = (
            membership.reward_program_id if membership else None
        )
        bonus.save(update_fields=("bonus_unit", "reward_program"))


class Migration(migrations.Migration):
    dependencies = [("cardapi", "0010_normalize_signup_bonus")]

    operations = [
        migrations.RunPython(correct_bonus_units, migrations.RunPython.noop),
    ]
