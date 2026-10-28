"""Punkte verteilen und verfallen lassen (ADR-002, ADR-003).

Jeder Zugang hat 100 Punkte. Er gibt sie an Einrichtungen oder an ein ganzes Thema und kann
jederzeit umverteilen. Gespeichert wird immer die ganze Verteilung auf einmal.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.access.models import Participant
from apps.points.models import POINTS_BUDGET, Allocation

TargetKind = Literal["f", "c"]


@dataclass(frozen=True, order=True)
class Target:
    """Ziel von Punkten: Einrichtung (``f``) oder Thema allgemein (``c``)."""

    kind: TargetKind
    pk: int

    @property
    def key(self) -> str:
        return f"{self.kind}-{self.pk}"

    @classmethod
    def of(cls, allocation: Allocation) -> "Target":
        if allocation.facility_id is not None:
            return cls("f", allocation.facility_id)
        if allocation.category_id is None:  # durch den Check-Constraint ausgeschlossen
            raise ValueError("Punktevergabe ohne Ziel")
        return cls("c", allocation.category_id)


class BudgetExceededError(ValueError):
    def __init__(self, total: int) -> None:
        super().__init__(f"{total} Punkte vergeben, erlaubt sind {POINTS_BUDGET}.")
        self.total = total


def expiry_cutoff() -> datetime:
    return timezone.now() - timedelta(days=settings.POINTS_EXPIRY_DAYS)


def active_allocations() -> QuerySet[Allocation]:
    """Alle noch gültigen Punkte; Grundlage für Ergebnisse und Dashboard."""
    return Allocation.objects.filter(participant__last_active_at__gte=expiry_cutoff())


def points_of(participant: Participant) -> dict[Target, int]:
    return {Target.of(a): a.points for a in Allocation.objects.filter(participant=participant)}


def save_distribution(participant: Participant, points: Mapping[Target, int]) -> None:
    """Ersetzt die Verteilung eines Zugangs vollständig. Ziele mit 0 Punkten entfallen."""
    wanted = {target: value for target, value in points.items() if value > 0}
    total = sum(wanted.values())
    if total > POINTS_BUDGET:
        raise BudgetExceededError(total)

    with transaction.atomic():
        # Zwei Tabs speichern nacheinander, nicht verschränkt.
        Participant.objects.select_for_update().filter(pk=participant.pk).get()
        Allocation.objects.filter(participant=participant).delete()
        Allocation.objects.bulk_create(
            Allocation(
                participant=participant,
                facility_id=target.pk if target.kind == "f" else None,
                category_id=target.pk if target.kind == "c" else None,
                points=value,
            )
            for target, value in sorted(wanted.items())
        )


def expire_points() -> int:
    """Löscht die Punkte aller Zugänge, die länger als die Verfallsfrist inaktiv sind."""
    deleted, _ = Allocation.objects.filter(participant__last_active_at__lt=expiry_cutoff()).delete()
    return deleted


def expire_points_of(participant: Participant, previous_active_at: datetime) -> None:
    if previous_active_at < expiry_cutoff():
        Allocation.objects.filter(participant=participant).delete()
