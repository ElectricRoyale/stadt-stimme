"""Legt im Demo-Modus die Demo-Codes aus ``data/demo/access_codes.txt`` an, einmalig."""

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.access.services import demo_codes_missing, load_demo_codes


class Command(BaseCommand):
    help = "Legt im Demo-Modus die Demo-Codes an, sofern noch keine Codes existieren."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEMO_MODE:
            self.stdout.write("Demo-Modus aus: keine Demo-Codes angelegt.")
            return
        if not demo_codes_missing():
            self.stdout.write("Codes vorhanden: Demo-Codes übersprungen.")
            return
        count = load_demo_codes(settings.DEMO_DATA_DIR / "access_codes.txt")
        self.stdout.write(f"{count} Demo-Codes angelegt.")
