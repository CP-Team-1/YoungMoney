import json

from django.core.management.base import BaseCommand, CommandError

from cardapi.services.cardapi import CardAPIClient, CardAPIError, import_cards_payload


class Command(BaseCommand):
    help = "Fetch and upsert specific CardAPI cards by slug."

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="+", help="One or more CardAPI card slugs")

    def handle(self, *args, **options):
        client = CardAPIClient()
        totals = None
        try:
            for slug in options["slugs"]:
                payload = client.get_card(slug)
                data = payload.get("data")
                normalized = payload if isinstance(data, list) else {"data": [data]}
                stats = import_cards_payload(normalized)
                if totals is None:
                    totals = stats.to_dict()
                else:
                    for key, value in stats.to_dict().items():
                        totals[key] += value
        except CardAPIError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(json.dumps(totals or {}, sort_keys=True)))
