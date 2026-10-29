from collections.abc import Callable

from django.http import HttpRequest

from apps.access.session import current_participant
from apps.points.models import POINTS_BUDGET
from apps.points.services import points_of


def points_left(request: HttpRequest) -> dict[str, Callable[[], int | None]]:
    """Freie Punkte für die Navigation („20 frei“); None ohne Zugang.

    Als Funktion übergeben, damit die Abfrage nur läuft, wenn ein Template den Wert nutzt.
    """

    def left() -> int | None:
        participant = current_participant(request)
        if participant is None:
            return None
        return POINTS_BUDGET - sum(points_of(participant).values())

    return {"points_left": left}
