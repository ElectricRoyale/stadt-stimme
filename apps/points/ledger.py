"""Punktebewegungen mit Ereignis (ADR-027).

Jede Änderung an ``Allocation`` schreibt in derselben Transaktion ein ``PointEvent``. Aufrufer
sperren vorher die Zeile des Zugangs (``select_for_update``), damit Speichern, Verfall und
Rückfluss für denselben Zugang nacheinander laufen.
"""

from collections.abc import Mapping
from datetime import datetime

from django.db.models import QuerySet
from django.utils import timezone

from apps.catalog.models import Measure
from apps.points.models import Allocation, PointEvent, PointEventKind
from apps.points.targets import Target


def event(
    participant_id: int,
    target: Target,
    delta: int,
    kind: PointEventKind,
    *,
    at: datetime,
    measure: Measure | None = None,
) -> PointEvent:
    return PointEvent(
        participant_id=participant_id,
        facility_id=target.facility_id,
        category_id=target.category_id,
        kind=kind,
        delta=delta,
        measure=measure,
        created_at=at,
    )


def change_events(
    participant_id: int,
    before: Mapping[Target, int],
    after: Mapping[Target, int],
    *,
    at: datetime,
) -> list[PointEvent]:
    """Ereignisse für eine neue Verteilung: mehr Punkte „vergeben“, weniger „entzogen“."""
    events = []
    for target in sorted(before.keys() | after.keys()):
        delta = after.get(target, 0) - before.get(target, 0)
        if delta:
            kind = PointEventKind.GRANTED if delta > 0 else PointEventKind.WITHDRAWN
            events.append(event(participant_id, target, delta, kind, at=at))
    return events


def remove(
    allocations: QuerySet[Allocation],
    kind: PointEventKind,
    *,
    measure: Measure | None = None,
) -> list[Allocation]:
    """Löscht die Vergaben und schreibt je Vergabe ein Ereignis mit negativem Delta."""
    removed = list(allocations)
    if not removed:
        return []
    now = timezone.now()
    PointEvent.objects.bulk_create(
        event(a.participant_id, Target.of(a), -a.points, kind, at=now, measure=measure)
        for a in removed
    )
    Allocation.objects.filter(pk__in=[a.pk for a in removed]).delete()
    return removed
