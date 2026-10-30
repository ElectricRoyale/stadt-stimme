from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "apps.notifications"
    verbose_name = "Benachrichtigungen"

    def ready(self) -> None:
        from apps.notifications import receivers  # noqa: F401  Signal-Empfänger registrieren
