from datetime import datetime
from typing import Any

from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from apps.access.models import Participant
from apps.access.signals import participant_active_again
from apps.catalog.models import Measure
from apps.points.returns import return_points, triggers_return
from apps.points.services import expire_points_of, withdraw_all

_PREVIOUS_STATUS = "_points_previous_status"


@receiver(participant_active_again)
def _expire_on_return(
    sender: Any, participant: Participant, previous_active_at: datetime, **kwargs: Any
) -> None:
    """Wer nach Ablauf der Frist zurückkommt, startet wieder mit 100 freien Punkten (ADR-003)."""
    expire_points_of(participant, previous_active_at)


@receiver(pre_save, sender=Measure)
def _remember_status(sender: Any, instance: Measure, raw: bool = False, **kwargs: Any) -> None:
    previous = None
    if instance.pk is not None and not raw:
        previous = Measure.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
    setattr(instance, _PREVIOUS_STATUS, previous)


@receiver(post_save, sender=Measure)
def _return_on_progress(sender: Any, instance: Measure, raw: bool = False, **kwargs: Any) -> None:
    """Gilt für jeden Weg: Admin, Verwaltungsseite und CSV-Import (ADR-027)."""
    if raw:  # Fixtures laden
        return
    if triggers_return(getattr(instance, _PREVIOUS_STATUS, None), instance.status):
        return_points(instance)


@receiver(pre_delete, sender=Participant)
def _withdraw_before_delete(sender: Any, instance: Participant, **kwargs: Any) -> None:
    """Das Log bleibt pseudonym erhalten; die Punkte zählen ab dem Löschen nicht mehr (L8)."""
    withdraw_all(instance.pk)
