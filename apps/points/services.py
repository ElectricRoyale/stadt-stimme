"""Punkte verteilen und verfallen lassen (ADR-003, ADR-011, ADR-027).

Jeder Zugang hat 100 Punkte. Er gibt sie an Einrichtungen oder an ein ganzes Thema und kann
jederzeit umverteilen. Gespeichert wird immer die ganze Verteilung auf einmal. Jede Änderung
landet zusätzlich als Ereignis im Log (``ledger``).
"""

from collections.abc import Mapping
from datetime import date, datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Facility
from apps.points import ledger
from apps.points.models import POINTS_BUDGET, Allocation, PointEvent, PointEventKind
from apps.points.targets import Target, TargetKind

__all__ = [
    "BudgetExceededError",
    "DoneFacilityError",
    "Target",
    "TargetKind",
    "active_allocations",
    "expire_points",
    "expire_points_of",
    "save_distribution",
]


class DoneFacilityError(ValueError):
    """Punkte an eine erledigte Einrichtung, z. B. aus einem Formular von vor dem Erledigen."""

    def __init__(self, names: list[str]) -> None:
        super().__init__(
            f"{', '.join(names)} ist inzwischen erledigt und nicht mehr wählbar. "
            "Bitte verteile diese Punkte neu."
        )


class BudgetExceededError(ValueError):
    def __init__(self, total: int) -> None:
        super().__init__(f"{total} Punkte vergeben, erlaubt sind {POINTS_BUDGET}.")
        self.total = total


def expiry_cutoff() -> datetime:
    return timezone.now() - timedelta(days=settings.POINTS_EXPIRY_DAYS)


def active_allocations() -> QuerySet[Allocation]:
    """Alle noch gültigen Punkte; Grundlage für Ergebnisse und Dashboard."""
    return Allocation.objects.filter(participant__last_active_at__gte=expiry_cutoff())


def valid_until(participant: Participant) -> date:
    """Letzter Tag, an dem die Punkte noch zählen; jeder Besuch verlängert die Frist (ADR-003)."""
    return timezone.localdate(participant.last_active_at) + timedelta(
        days=settings.POINTS_EXPIRY_DAYS
    )


def last_saved_at(participant: Participant) -> datetime | None:
    """Zeitpunkt der letzten gespeicherten Verteilung; None, solange nichts vergeben ist."""
    latest = Allocation.objects.filter(participant=participant).order_by("-updated_at").first()
    return latest.updated_at if latest else None


def points_of(participant: Participant) -> dict[Target, int]:
    return {Target.of(a): a.points for a in Allocation.objects.filter(participant=participant)}


def _lock(participant_id: int) -> Participant | None:
    return Participant.objects.select_for_update().filter(pk=participant_id).first()


def save_distribution(participant: Participant, points: Mapping[Target, int]) -> None:
    """Ersetzt die Verteilung eines Zugangs vollständig. Ziele mit 0 Punkten entfallen."""
    wanted = {target: value for target, value in points.items() if value > 0}
    total = sum(wanted.values())
    if total > POINTS_BUDGET:
        raise BudgetExceededError(total)

    with transaction.atomic():
        done = Facility.objects.filter(
            pk__in=[t.pk for t in wanted if t.kind == "f"], done_at__isnull=False
        )
        if done.exists():
            raise DoneFacilityError(sorted(done.values_list("name", flat=True)))
        # Zwei Tabs, Verfall und Rückfluss laufen für denselben Zugang nacheinander.
        _lock(participant.pk)
        before = points_of(participant)
        Allocation.objects.filter(participant=participant).delete()
        Allocation.objects.bulk_create(
            Allocation(
                participant=participant,
                facility_id=target.facility_id,
                category_id=target.category_id,
                points=value,
            )
            for target, value in sorted(wanted.items())
        )
        PointEvent.objects.bulk_create(
            ledger.change_events(participant.pk, before, wanted, at=timezone.now())
        )


def expire_points() -> int:
    """Entzieht die Punkte aller Zugänge, die länger als die Verfallsfrist inaktiv sind.

    Idempotent: Ein zweiter Lauf findet nichts mehr. Jeder Zugang in einer eigenen kurzen
    Transaktion; wer zwischendurch zurückkommt, behält seine Punkte.
    """
    stale = (
        Allocation.objects.filter(participant__last_active_at__lt=expiry_cutoff())
        .values_list("participant_id", flat=True)
        .distinct()
    )
    return sum(_expire(participant_id) for participant_id in list(stale))


def _expire(participant_id: int) -> int:
    with transaction.atomic():
        participant = _lock(participant_id)
        if participant is None or participant.last_active_at >= expiry_cutoff():
            return 0
        allocations = Allocation.objects.filter(participant_id=participant_id)
        return len(ledger.remove(allocations, PointEventKind.EXPIRED))


def expire_points_of(participant: Participant, previous_active_at: datetime) -> None:
    """Wer nach Ablauf der Frist zurückkommt, startet mit 100 freien Punkten (ADR-003)."""
    if previous_active_at < expiry_cutoff():
        with transaction.atomic():
            _lock(participant.pk)
            allocations = Allocation.objects.filter(participant=participant)
            ledger.remove(allocations, PointEventKind.EXPIRED)


def withdraw_all(participant_id: int) -> None:
    """Entzieht alle Punkte, z. B. bevor ein Zugang gelöscht wird (L8)."""
    with transaction.atomic():
        _lock(participant_id)
        allocations = Allocation.objects.filter(participant_id=participant_id)
        ledger.remove(allocations, PointEventKind.WITHDRAWN)
