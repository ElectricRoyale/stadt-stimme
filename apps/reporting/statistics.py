"""Kennzahlen für das Dashboard: Bürgerpunkte gegen Ausgaben je Thema (ADR-006, ADR-011).

Bürgerpunkte zählen nur, solange sie nicht verfallen sind (ADR-003). Verglichen werden Anteile:
Anteil eines Themas an allen Bürgerpunkten gegen seinen Anteil an den Ist-Ausgaben des letzten
abgeschlossenen Haushaltsjahres.
"""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.catalog.models import Category, Expenditure, ExpenditureKind, Facility
from apps.points.services import Target, active_allocations


def share(part: float | Decimal, total: float | Decimal) -> int:
    """Ganzzahliger Prozentanteil; 0, solange es noch nichts zu verteilen gibt."""
    return round(float(part) / float(total) * 100) if total else 0


@dataclass(frozen=True)
class PlaceStat:
    """Ziel von Punkten: eine Einrichtung oder ein Thema als Ganzes (``facility`` ist dann None)."""

    target: Target
    name: str
    category: Category
    facility: Facility | None
    points: int
    share: int
    mine: int

    @property
    def is_general(self) -> bool:
        return self.facility is None


@dataclass(frozen=True)
class ThemeStat:
    category: Category
    general_share: int
    places_share: int
    spend: Decimal
    spend_share: int
    mine: int

    @property
    def citizen_share(self) -> int:
        return self.general_share + self.places_share

    @property
    def gap(self) -> int:
        return self.citizen_share - self.spend_share


@dataclass(frozen=True)
class Overview:
    themes: list[ThemeStat]
    places: list[PlaceStat]
    total_points: int
    participants: int
    fiscal_year: int | None
    mine_used: int

    @property
    def top_theme(self) -> ThemeStat | None:
        ranked = [t for t in self.themes if t.citizen_share > 0]
        return max(ranked, key=lambda t: t.citizen_share, default=None)

    @property
    def biggest_gap(self) -> ThemeStat | None:
        """Thema, das Bürgern am meisten mehr wert ist, als die Stadt dafür ausgibt."""
        ranked = [t for t in self.themes if t.gap > 0]
        return max(ranked, key=lambda t: t.gap, default=None)

    @property
    def scale_max(self) -> int:
        """Gemeinsamer Maßstab der Balken: Bürger, Stadt und eigene Punkte bleiben vergleichbar."""
        values = [max(t.citizen_share, t.spend_share, t.mine) for t in self.themes]
        return max(values, default=0) or 1


def build_overview(mine: Mapping[Target, int] | None = None) -> Overview:
    mine = mine or {}
    allocations = active_allocations()
    by_facility = _sum_by(allocations.filter(facility__isnull=False), "facility_id")
    by_category = _sum_by(allocations.filter(category__isnull=False), "category_id")
    total = sum(by_facility.values()) + sum(by_category.values())

    fiscal_year = _last_closed_fiscal_year()
    spend_by_category = _spend_by_category(fiscal_year)
    spend_total = sum(spend_by_category.values(), Decimal(0))

    facilities = list(
        Facility.objects.select_related("category").prefetch_related("measures").order_by("name")
    )
    categories = list(Category.objects.filter(facilities__isnull=False).distinct().order_by("name"))
    places_points: dict[int, int] = defaultdict(int)
    mine_by_category: dict[int, int] = defaultdict(int)
    for facility in facilities:
        places_points[facility.category_id] += by_facility.get(facility.pk, 0)
        mine_by_category[facility.category_id] += mine.get(Target("f", facility.pk), 0)

    themes = [
        ThemeStat(
            category=c,
            general_share=share(by_category.get(c.pk, 0), total),
            places_share=share(places_points[c.pk], total),
            spend=spend_by_category.get(c.pk, Decimal(0)),
            spend_share=share(spend_by_category.get(c.pk, Decimal(0)), spend_total),
            mine=mine_by_category[c.pk] + mine.get(Target("c", c.pk), 0),
        )
        for c in categories
    ]
    places = [
        PlaceStat(
            target=Target("f", f.pk),
            name=f.name,
            category=f.category,
            facility=f,
            points=by_facility.get(f.pk, 0),
            share=share(by_facility.get(f.pk, 0), total),
            mine=mine.get(Target("f", f.pk), 0),
        )
        for f in facilities
    ] + [
        PlaceStat(
            target=Target("c", c.pk),
            name=f"{c.name} allgemein",
            category=c,
            facility=None,
            points=by_category.get(c.pk, 0),
            share=share(by_category.get(c.pk, 0), total),
            mine=mine.get(Target("c", c.pk), 0),
        )
        for c in categories
    ]
    places.sort(key=lambda p: (-p.points, p.name))
    return Overview(
        themes=themes,
        places=places,
        total_points=total,
        participants=allocations.values("participant").distinct().count(),
        fiscal_year=fiscal_year,
        mine_used=sum(mine.values()),
    )


def _sum_by(queryset: object, field: str) -> dict[int, int]:
    rows = queryset.values(field).annotate(total=Sum("points"))  # type: ignore[attr-defined]
    return {row[field]: row["total"] for row in rows}


def _last_closed_fiscal_year() -> int | None:
    year: int | None = (
        Expenditure.objects.filter(
            kind=ExpenditureKind.ACTUAL, fiscal_year__lt=timezone.localdate().year
        )
        .order_by("-fiscal_year")
        .values_list("fiscal_year", flat=True)
        .first()
    )
    return year


def _spend_by_category(fiscal_year: int | None) -> dict[int, Decimal]:
    if fiscal_year is None:
        return {}
    rows = (
        Expenditure.objects.filter(kind=ExpenditureKind.ACTUAL, fiscal_year=fiscal_year)
        .values("facility__category_id")
        .annotate(total=Sum("amount"))
    )
    return {row["facility__category_id"]: row["total"] for row in rows}
