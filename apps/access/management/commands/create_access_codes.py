"""Erzeugt Aktivierungscodes und gibt sie genau einmal als CSV aus (Seriennummer, Code).

Bis der Druckexport (M5) abgestimmt ist, dient das als Skript für Test-Codes.
"""

import csv
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.access.codes import format_code
from apps.access.services import create_codes

MAX_COUNT = 100_000


class Command(BaseCommand):
    help = "Erzeugt Aktivierungscodes. Der Klartext wird nur hier ausgegeben, nie gespeichert."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("count", type=int, help="Anzahl der Codes")
        parser.add_argument("--batch", required=True, help="Name der Charge, z. B. 'Test 2026-11'")

    def handle(self, *args: Any, **options: Any) -> None:
        count: int = options["count"]
        if not 1 <= count <= MAX_COUNT:
            raise CommandError(f"Anzahl muss zwischen 1 und {MAX_COUNT} liegen.")

        issued = create_codes(count, batch=options["batch"])
        writer = csv.writer(self.stdout)
        writer.writerow(["serial", "code"])
        for item in issued:
            writer.writerow([item.serial, format_code(item.code)])
        self.stderr.write(
            f"{count} Codes erzeugt. Der Klartext ist nur in dieser Ausgabe enthalten."
        )
