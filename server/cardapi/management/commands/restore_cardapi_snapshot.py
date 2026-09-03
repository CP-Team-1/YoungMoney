import json

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cardapi.models import (
    CardRewardProgram,
    CreditCard,
    Issuer,
    RewardCategory,
    RewardCategoryAlias,
    RewardProgram,
    RewardProgramUnlock,
    RewardTransferRoute,
)


DEFAULT_SNAPSHOT = "cardapi/data/catalog_snapshot_2026-09-02.json"


class Command(BaseCommand):
    help = "Replace CardAPI catalog tables from a committed Django snapshot."

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", default=DEFAULT_SNAPSHOT)
        parser.add_argument(
            "--confirm-replace",
            action="store_true",
            help="Required acknowledgement that existing CardAPI catalog data is replaced.",
        )

    def handle(self, *args, **options):
        if not options["confirm_replace"]:
            raise CommandError(
                "Restoration replaces existing CardAPI catalog data. "
                "Re-run with --confirm-replace."
            )

        with transaction.atomic():
            RewardTransferRoute.objects.all().delete()
            RewardProgramUnlock.objects.all().delete()
            CardRewardProgram.objects.all().delete()
            CreditCard.objects.all().delete()
            RewardProgram.objects.all().delete()
            RewardCategoryAlias.objects.all().delete()
            RewardCategory.objects.update(parent=None)
            RewardCategory.objects.all().delete()
            Issuer.objects.all().delete()
            call_command("loaddata", options["path"], verbosity=0)

        output = {
            "snapshot": options["path"],
            "issuers": Issuer.objects.count(),
            "cards": CreditCard.objects.count(),
            "categories": RewardCategory.objects.count(),
            "reward_programs": RewardProgram.objects.count(),
            "transfer_routes": RewardTransferRoute.objects.count(),
        }
        self.stdout.write(self.style.SUCCESS(json.dumps(output, sort_keys=True)))
