from typing import Any

from django.core.management.base import BaseCommand

from apps.points.services import expire_points


class Command(BaseCommand):
    help = "Entzieht Punkte von Zugängen, die länger als die Verfallsfrist inaktiv sind (ADR-003)."

    def handle(self, *args: Any, **options: Any) -> None:
        deleted = expire_points()
        self.stdout.write(self.style.SUCCESS(f"{deleted} verfallene Punktevergaben entzogen."))
