import json

from django.core.management.base import BaseCommand, CommandError

from cardapi.services.cardapi import CardAPIError
from cardapi.services.reward_programs import load_reward_program_file


class Command(BaseCommand):
    help = "Import reviewed reward programs, card capabilities, and portfolio unlocks."

    def add_arguments(self, parser):
        parser.add_argument("path")

    def handle(self, *args, **options):
        try:
            stats = load_reward_program_file(options["path"])
        except CardAPIError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(json.dumps(stats, sort_keys=True)))
