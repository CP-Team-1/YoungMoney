import json

from django.core.management.base import BaseCommand, CommandError

from cardapi.services.coverage import MISSING, build_coverage_report


class Command(BaseCommand):
    help = "Report missing, incomplete, stale, and unavailable CardAPI data."

    def add_arguments(self, parser):
        parser.add_argument("--country", choices=("US", "CA"))
        parser.add_argument("--slug", action="append", dest="slugs")
        parser.add_argument("--limit", type=int)
        parser.add_argument("--stale-after-days", type=int, default=90)
        parser.add_argument(
            "--unavailable",
            action="append",
            choices=("perks", "statement_credits"),
            default=[],
            help="Feature known to be unavailable on the current CardAPI plan.",
        )
        parser.add_argument("--format", choices=("table", "json"), default="table")

    def handle(self, *args, **options):
        if options["limit"] is not None and options["limit"] < 1:
            raise CommandError("--limit must be at least 1.")
        if options["stale_after_days"] < 0:
            raise CommandError("--stale-after-days cannot be negative.")

        report = build_coverage_report(
            country=options["country"],
            slugs=options["slugs"],
            limit=options["limit"],
            stale_after_days=options["stale_after_days"],
            unavailable=options["unavailable"],
        )
        if options["format"] == "json":
            self.stdout.write(json.dumps(report, indent=2, sort_keys=True))
            return

        summary = report["summary"]
        self.stdout.write(
            f"Cards: {summary['cards']} | "
            f"recommendation-ready: {summary['recommendation_ready']} | "
            f"stale: {summary['stale_cards']}"
        )
        for card in report["cards"]:
            missing = [
                f"{field}={status}"
                for field, status in card["statuses"].items()
                if status != "present"
            ]
            readiness = "READY" if card["recommendation_ready"] else "NOT READY"
            details = ", ".join(missing) if missing else "all tracked fields present"
            self.stdout.write(f"{readiness} | {card['slug']} | {details}")

        if not report["cards"]:
            self.stdout.write(self.style.WARNING("No cards matched the filters."))
        elif summary["status_totals"][MISSING]:
            self.stdout.write(
                self.style.WARNING(
                    f"Missing field instances: {summary['status_totals'][MISSING]}"
                )
            )
