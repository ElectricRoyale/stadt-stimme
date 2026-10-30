"""Tägliche Aufgaben in fester Reihenfolge; der Scheduler in docker compose ruft das auf.

Erst warnen, dann verfallen lassen: Wer heute die Warnung bekäme und morgen verfällt, bekommt
sie so noch rechtzeitig. Beide Schritte sind idempotent, ein doppelter Lauf schadet nicht.
"""

import logging
from typing import Any

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

DAILY_COMMANDS = ["send_expiry_warnings", "expire_points"]


class Command(BaseCommand):
    help = "Verfallswarnungen verschicken und abgelaufene Punkte entziehen (ADR-003)."

    def handle(self, *args: Any, **options: Any) -> None:
        failed = []
        for name in DAILY_COMMANDS:
            try:
                call_command(name, stdout=self.stdout, stderr=self.stderr)
            except Exception:
                # Ein Fehler beim Warnen darf den Verfall nicht aufhalten (und umgekehrt).
                logger.exception("Tägliche Aufgabe %s fehlgeschlagen", name)
                failed.append(name)
        if failed:
            raise CommandError(f"Fehlgeschlagen: {', '.join(failed)}")
