import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from cardapi.services.cardapi import CardAPIError, import_curated_payload


class Command(BaseCommand):
    help = "Fill missing card data from a reviewed JSON file."

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path)

    def handle(self, *args, **options):
        path = options["path"]
        try:
            with path.open(encoding="utf-8") as source:
                payload = json.load(source)
            stats = import_curated_payload(payload)
        except (OSError, json.JSONDecodeError, CardAPIError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(json.dumps(stats, sort_keys=True)))
