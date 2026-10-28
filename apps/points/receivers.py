from datetime import datetime
from typing import Any

from django.dispatch import receiver

from apps.access.models import Participant
from apps.access.signals import participant_active_again
from apps.points.services import expire_points_of


@receiver(participant_active_again)
def _expire_on_return(
    sender: Any, participant: Participant, previous_active_at: datetime, **kwargs: Any
) -> None:
    """Wer nach Ablauf der Frist zurückkommt, startet wieder mit 100 freien Punkten (ADR-003)."""
    expire_points_of(participant, previous_active_at)
