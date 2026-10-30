from typing import Any

from django.core.management.base import BaseCommand

from apps.notifications.expiry import send_expiry_warnings


class Command(BaseCommand):
    help = "Warnt per E-Mail vor dem Verfall der Punkte (ADR-003, ADR-004). Idempotent."

    def handle(self, *args: Any, **options: Any) -> None:
        sent = send_expiry_warnings()
        self.stdout.write(self.style.SUCCESS(f"{sent} Verfallswarnungen verschickt."))
