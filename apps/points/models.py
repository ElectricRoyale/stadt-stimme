"""Punkte eines Zugangs: an eine Einrichtung oder an ein ganzes Thema (ADR-011, ADR-027)."""

from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Category, Facility

POINTS_BUDGET = 100


class Allocation(models.Model):
    """Aktueller Stand: so viele Punkte gibt ein Zugang einem Ziel. Null Punkte = keine Zeile."""

    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="allocations",
        verbose_name="Zugang",
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="allocations",
        verbose_name="Einrichtung",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="allocations",
        verbose_name="Thema allgemein",
        null=True,
        blank=True,
    )
    points = models.PositiveSmallIntegerField(
        "Punkte", validators=[MinValueValidator(1), MaxValueValidator(POINTS_BUDGET)]
    )
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "Punktevergabe"
        verbose_name_plural = "Punktevergaben"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(facility__isnull=False, category__isnull=True)
                    | Q(facility__isnull=True, category__isnull=False)
                ),
                name="allocation_exactly_one_target",
                violation_error_message=(
                    "Punkte gehen entweder an eine Einrichtung oder an ein Thema."
                ),
            ),
            models.CheckConstraint(
                condition=Q(points__gte=1) & Q(points__lte=POINTS_BUDGET),
                name="allocation_points_in_budget",
                violation_error_message="Punkte müssen zwischen 1 und 100 liegen.",
            ),
            models.UniqueConstraint(
                fields=["participant", "facility"],
                condition=Q(facility__isnull=False),
                name="allocation_unique_facility",
            ),
            models.UniqueConstraint(
                fields=["participant", "category"],
                condition=Q(category__isnull=False),
                name="allocation_unique_category",
            ),
        ]

    def __str__(self) -> str:
        target = self.facility or f"{self.category} allgemein"
        return f"{self.points} P. → {target}"


class PointEventKind(models.TextChoices):
    GRANTED = "vergeben", "vergeben"
    WITHDRAWN = "entzogen", "entzogen"
    RETURNED = "zurueckgegeben", "zurückgegeben"
    EXPIRED = "verfallen", "verfallen"


class PointEvent(models.Model):
    """Unveränderliches Ereignis: so viele Punkte kamen zu einem Ziel hinzu oder gingen (ADR-027).

    Der aktuelle Stand bleibt ``Allocation``; Stichtagswerte rechnet man aus diesem Log nach.
    Der Zugang ist ohne Fremdschlüssel-Constraint verknüpft, damit das Log erhalten bleibt,
    wenn ein Zugang gelöscht wird. Die Datenbank verbietet UPDATE und DELETE (Migration 0002).
    """

    participant = models.ForeignKey(
        Participant,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="point_events",
        verbose_name="Zugang",
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="point_events",
        verbose_name="Einrichtung",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="point_events",
        verbose_name="Thema allgemein",
        null=True,
        blank=True,
    )
    kind = models.CharField("Art", max_length=20, choices=PointEventKind.choices)
    delta = models.SmallIntegerField("Änderung")
    measure = models.ForeignKey(
        "catalog.Measure",
        on_delete=models.PROTECT,
        related_name="point_events",
        verbose_name="Anlass (Maßnahme)",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("Zeitpunkt", default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Punkte-Ereignis"
        verbose_name_plural = "Punkte-Ereignisse"
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["participant", "kind", "created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(facility__isnull=False, category__isnull=True)
                    | Q(facility__isnull=True, category__isnull=False)
                ),
                name="point_event_exactly_one_target",
            ),
            models.CheckConstraint(condition=~Q(delta=0), name="point_event_delta_not_zero"),
            models.CheckConstraint(
                condition=(
                    Q(kind=PointEventKind.GRANTED, delta__gt=0)
                    | (~Q(kind=PointEventKind.GRANTED) & Q(delta__lt=0))
                ),
                name="point_event_sign_matches_kind",
            ),
        ]

    def __str__(self) -> str:
        target = self.facility or f"{self.category} allgemein"
        return f"{self.delta:+d} P. {self.get_kind_display()} → {target}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk is not None:
            raise ImmutableEventError
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ImmutableEventError


class ImmutableEventError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Punkte-Ereignisse sind unveränderlich.")
