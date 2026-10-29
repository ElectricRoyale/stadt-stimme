"""Lädt im Demo-Modus die fiktiven Testdaten für Mannheim, aber nur in einen leeren Katalog.

So bleiben Änderungen aus der Vorführung bei einem Neustart erhalten.
"""

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.catalog.management.commands.import_catalog import write_report
from apps.catalog.services import catalog_is_empty, import_catalog


class Command(BaseCommand):
    help = "Lädt im Demo-Modus die Demo-Daten, sofern der Katalog leer ist."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEMO_MODE:
            self.stdout.write("Demo-Modus aus: keine Demo-Daten geladen.")
            return
        if not catalog_is_empty():
            self.stdout.write("Katalog enthält bereits Daten: Demo-Daten übersprungen.")
            return
        write_report(self, import_catalog(settings.DEMO_DATA_DIR))
