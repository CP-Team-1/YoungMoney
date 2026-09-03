import json

from django.core.management.base import BaseCommand, CommandError

from cardapi.services.cardapi import CardAPIDataError
from cardapi.services.transfer_partners import load_transfer_partner_file


class Command(BaseCommand):
    help = "Import reviewed reward transfer partners and ratios."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument(
            "--non-authoritative",
            action="store_true",
            help="Do not deactivate omitted routes for included source programs.",
        )

    def handle(self, *args, **options):
        try:
            stats = load_transfer_partner_file(
                options["path"],
                authoritative=not options["non_authoritative"],
            )
        except CardAPIDataError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(stats, sort_keys=True))
