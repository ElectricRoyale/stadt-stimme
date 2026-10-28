from django.apps import AppConfig


class PointsConfig(AppConfig):
    name = "apps.points"
    verbose_name = "Punkte"

    def ready(self) -> None:
        from apps.points import receivers  # noqa: F401  Signal-Empfänger registrieren
