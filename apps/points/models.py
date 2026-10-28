"""Punkte eines Zugangs: an eine Einrichtung oder an ein ganzes Thema (ADR-002)."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

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
