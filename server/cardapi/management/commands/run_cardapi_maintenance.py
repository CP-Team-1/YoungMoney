import json

from django.core.management.base import BaseCommand, CommandError

from cardapi.services.cardapi import (
    CardAPIClient,
    CardAPIDataError,
    CardAPIError,
    ImportStats,
    import_cards_payload,
)
from cardapi.services.coverage import build_coverage_report


class Command(BaseCommand):
    help = "Synchronize the complete CardAPI catalog and report coverage."

    def add_arguments(self, parser):
        parser.add_argument("--country", choices=("US", "CA"), default="US")
        parser.add_argument("--page-size", type=int, default=100)
        parser.add_argument("--max-pages", type=int, default=100)
        parser.add_argument("--stale-after-days", type=int, default=90)
        parser.add_argument(
            "--unavailable",
            action="append",
            choices=("perks", "statement_credits"),
            default=[],
        )

    def handle(self, *args, **options):
        page_size = options["page_size"]
        max_pages = options["max_pages"]
        stale_after_days = options["stale_after_days"]
        if not 1 <= page_size <= 100:
            raise CommandError("--page-size must be between 1 and 100.")
        if max_pages < 1:
            raise CommandError("--max-pages must be at least 1.")
        if stale_after_days < 0:
            raise CommandError("--stale-after-days cannot be negative.")

        totals = ImportStats().to_dict()
        pages_fetched = 0
        cards_received = 0
        offset = 0
        page_signatures = set()
        last_page_was_full = False

        try:
            client = CardAPIClient()
            while pages_fetched < max_pages:
                payload = client.get_cards(
                    limit=page_size,
                    offset=offset,
                    country=options["country"],
                )
                records = (
                    payload.get("data") if isinstance(payload, dict) else None
                )
                if not isinstance(records, list):
                    raise CardAPIDataError(
                        "CardAPI list responses must contain a data array."
                    )
                if not records:
                    last_page_was_full = False
                    break

                if any(
                    not isinstance(record, dict) or not record.get("slug")
                    for record in records
                ):
                    raise CardAPIDataError(
                        "CardAPI pagination returned an invalid card row."
                    )
                signature = tuple(sorted(str(record["slug"]) for record in records))
                if signature in page_signatures:
                    raise CardAPIDataError(
                        "CardAPI pagination repeated a previously received page."
                    )
                page_signatures.add(signature)

                stats = import_cards_payload(
                    payload,
                    authoritative_child_data=False,
                )
                for field, value in stats.to_dict().items():
                    totals[field] += value
                pages_fetched += 1
                cards_received += len(records)
                offset += len(records)
                last_page_was_full = len(records) == page_size
                if not last_page_was_full:
                    break
        except CardAPIError as exc:
            raise CommandError(
                f"Maintenance stopped at offset {offset} after "
                f"{pages_fetched} completed pages: {exc}"
            ) from exc

        if last_page_was_full and pages_fetched == max_pages:
            raise CommandError(
                "CardAPI pagination reached --max-pages before finding the end. "
                "Increase the safety limit after confirming the expected catalog size."
            )

        coverage = build_coverage_report(
            country=options["country"],
            stale_after_days=stale_after_days,
            unavailable=options["unavailable"],
        )
        output = {
            "country": options["country"],
            "sync": {
                "pages_fetched": pages_fetched,
                "cards_received": cards_received,
                **totals,
            },
            "coverage": coverage,
        }
        self.stdout.write(self.style.SUCCESS(json.dumps(output, sort_keys=True)))
