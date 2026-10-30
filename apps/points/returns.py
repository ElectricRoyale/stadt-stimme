"""Rückfluss: Geht eine Maßnahme in Umsetzung, bekommen die Unterstützer ihrer Einrichtung die
Punkte zurück und können sie neu verteilen (ADR-027, ersetzt „kein Rückfluss“ aus ADR-011).

Punkte an ein ganzes Thema bleiben stehen; sie gelten keiner einzelnen Einrichtung.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Measure, MeasureStatus
from apps.points import ledger
from apps.points.models import Allocation, PointEvent, PointEventKind
from apps.points.signals import points_returned

# Status einer Maßnahme, bei deren Erreichen die Punkte ihrer Einrichtung zurückfließen.
RETURN_STATUSES = frozenset({MeasureStatus.IN_PROGRESS})
RECENT_DAYS = 30


@dataclass(frozen=True)
class ReturnedPoints:
    participant_id: int
    points: int


def triggers_return(previous: str | None, current: str) -> bool:
    return current in RETURN_STATUSES and previous not in RETURN_STATUSES


def return_points(measure: Measure) -> list[ReturnedPoints]:
    """Gibt alle Punkte auf der Einrichtung der Maßnahme an ihre Unterstützer zurück.

    Läuft in einer Transaktion: Zugänge sperren (feste Reihenfolge gegen Deadlocks), Ereignis
    „zurückgegeben“ schreiben, Vergaben löschen. Benachrichtigt wird erst nach dem Commit.
    """
    with transaction.atomic():
        supporters = Allocation.objects.filter(facility_id=measure.facility_id)
        ids = sorted(set(supporters.values_list("participant_id", flat=True)))
        list(Participant.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
        removed = ledger.remove(
            supporters.filter(participant_id__in=ids), PointEventKind.RETURNED, measure=measure
        )
        returns = [ReturnedPoints(a.participant_id, a.points) for a in removed]
        if returns:
            transaction.on_commit(
                lambda: points_returned.send(sender=Measure, returns=returns, measure=measure)
            )
    return returns


@dataclass(frozen=True)
class RecentChange:
    """Punkte, die einem Zugang ohne eigenes Zutun genommen wurden (Rückfluss oder Verfall)."""

    kind: str
    points: int
    target_name: str
    measure_title: str
    at: datetime


def recent_changes(participant: Participant, days: int = RECENT_DAYS) -> list[RecentChange]:
    """Zurückgeflossene und verfallene Punkte der letzten Tage, neueste zuerst (L6)."""
    since = timezone.now() - timedelta(days=days)
    events = (
        PointEvent.objects.filter(
            participant=participant,
            kind__in=[PointEventKind.RETURNED, PointEventKind.EXPIRED],
            created_at__gte=since,
        )
        .select_related("facility", "category", "measure")
        .order_by("-created_at", "-id")
    )
    return [
        RecentChange(
            kind=e.kind,
            points=-e.delta,
            target_name=e.facility.name if e.facility else f"{e.category} allgemein",
            measure_title=e.measure.title if e.measure else "",
            at=e.created_at,
        )
        for e in events
    ]
