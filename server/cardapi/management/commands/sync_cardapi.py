import json

from django.core.management.base import BaseCommand, CommandError

from cardapi.services.cardapi import CardAPIClient, CardAPIError, import_cards_payload


class Command(BaseCommand):
    help = "Fetch a small page of cards from CardAPI and upsert it locally."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--country", choices=("US", "CA"))
        parser.add_argument(
            "--authoritative-child-data",
            action="store_true",
            help=(
                "Allow missing reward rates and signup bonuses to be marked inactive. "
                "Do not use this with incomplete free-tier responses."
            ),
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        offset = options["offset"]
        if not 1 <= limit <= 100:
            raise CommandError("--limit must be between 1 and 100.")
        if offset < 0:
            raise CommandError("--offset cannot be negative.")

        try:
            payload = CardAPIClient().get_cards(
                limit=limit,
                offset=offset,
                country=options.get("country"),
            )
            stats = import_cards_payload(
                payload,
                authoritative_child_data=options["authoritative_child_data"],
            )
        except CardAPIError as exc:
            raise CommandError(str(exc)) from exc

        output = json.dumps(stats.to_dict(), sort_keys=True)
        self.stdout.write(self.style.SUCCESS(output))
