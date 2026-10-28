"""Legt im Demo-Modus idempotent einen Admin-Zugang an.

Das finale Admin-Login-Konzept ist zurückgestellt (MVP-Plan, M1). Bis dahin dient dieser
Zugang nur der lokalen Vorführung; außerhalb des Demo-Modus tut der Befehl nichts.
"""

import os
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Legt im Demo-Modus einen Admin aus DEMO_ADMIN_USERNAME/DEMO_ADMIN_PASSWORD an."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEMO_MODE:
            self.stdout.write("Demo-Modus aus: kein Demo-Admin angelegt.")
            return

        username = os.environ.get("DEMO_ADMIN_USERNAME", "")
        password = os.environ.get("DEMO_ADMIN_PASSWORD", "")
        if not username or not password:
            raise CommandError("DEMO_ADMIN_USERNAME und DEMO_ADMIN_PASSWORD müssen gesetzt sein.")

        user_model = get_user_model()
        if user_model.objects.filter(username=username).exists():
            self.stdout.write(f"Demo-Admin {username!r} existiert bereits.")
            return

        user_model.objects.create_superuser(username=username, email="", password=password)
        self.stdout.write(self.style.SUCCESS(f"Demo-Admin {username!r} angelegt."))
