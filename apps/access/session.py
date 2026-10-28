"""Sitzung eines Zugangs. Getrennt von Djangos User-Login, der nur für den Admin gilt."""

from django.http import HttpRequest

from apps.access.models import Participant
from apps.access.services import active_participant

SESSION_KEY = "access_participant_id"
_CACHE_ATTR = "_access_participant"


def log_in(request: HttpRequest, participant: Participant) -> None:
    request.session.cycle_key()  # neue Sitzungs-ID gegen Session Fixation
    request.session[SESSION_KEY] = participant.pk


def log_out(request: HttpRequest) -> None:
    request.session.flush()


def current_participant(request: HttpRequest) -> Participant | None:
    """Zugang der laufenden Sitzung; pro Request nur einmal aus der Datenbank geladen."""
    if not hasattr(request, _CACHE_ATTR):
        participant_id = request.session.get(SESSION_KEY)
        participant = (
            active_participant(participant_id) if isinstance(participant_id, int) else None
        )
        setattr(request, _CACHE_ATTR, participant)
    cached: Participant | None = getattr(request, _CACHE_ATTR)
    return cached
