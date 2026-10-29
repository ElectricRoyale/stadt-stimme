"""Ergebnisse „Wunsch und Haushalt“: Lücke je Einrichtung und je Thema (ADR-006, ADR-013).

Die Lücke ist der Anteil an allen Bürgerpunkten minus der Anteil an den Ist-Ausgaben des letzten
abgeschlossenen Haushaltsjahres, in Prozentpunkten. Positiv heißt: Bürgern ist es wichtiger, als
es im Haushalt abgebildet ist.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from django.db.models import Sum

from apps.catalog.models import Category, Expenditure, ExpenditureKind, Facility
from apps.reporting.statistics import Overview, share

GapTone = Literal["citizens", "city", "even"]


def signed(value: int) -> str:
    """Lücke mit Vorzeichen: +19, \u221229 (echtes Minus), \u00b10."""
    sign = "+" if value > 0 else "\u2212" if value < 0 else "\u00b1"
    return f"{sign}{abs(value)}"


@dataclass(frozen=True)
class GapRow:
    """Eine Einrichtung oder ein ganzes Thema (``facility`` ist dann None)."""

    key: str
    name: str
    category: Category
    facility: Facility | None
    wish: int
    spend: int
    mine: int

    @property
    def is_theme(self) -> bool:
        return self.facility is None

    @property
    def gap(self) -> int:
        return self.wish - self.spend

    @property
    def gap_text(self) -> str:
        return signed(self.gap)

    @property
    def tone(self) -> GapTone:
        return "citizens" if self.gap > 0 else "city" if self.gap < 0 else "even"

    @property
    def kicker(self) -> str:
        if self.is_theme:
            return "Ganzes Thema, alle Einrichtungen und „allgemein“"
        return self.category.name

    @property
    def summary(self) -> str:
        if self.gap > 0:
            return "Den Bürgern ist das wichtiger, als es im Haushalt abgebildet ist."
        if self.gap < 0:
            return "Hier gibt die Stadt mehr Geld aus, als es dem Wunsch der Bürger entspricht."
        return "Wunsch und Haushalt liegen gleichauf."


@dataclass(frozen=True)
class Results:
    places: list[GapRow]
    themes: list[GapRow]
    fiscal_year: int | None
    total_points: int

    @property
    def rows(self) -> list[GapRow]:
        return self.places + self.themes

    @property
    def scale_max(self) -> int:
        return max((max(r.wish, r.spend) for r in self.rows), default=0) or 1

    def select(self, key: str | None) -> GapRow | None:
        """Gewählte Zeile; sonst der Ort mit der größten Lücke."""
        by_key = {r.key: r for r in self.rows}
        if key in by_key:
            return by_key[key]
        return next(iter(self.rows), None)


def build_results(overview: Overview) -> Results:
    spend = _spend_by_facility(overview.fiscal_year)
    spend_total = sum(spend.values(), Decimal(0))
    places = [
        GapRow(
            key=p.target.key,
            name=p.name,
            category=p.category,
            facility=p.facility,
            wish=p.share,
            spend=share(spend.get(p.facility.pk, Decimal(0)), spend_total),
            mine=p.mine,
        )
        for p in overview.places
        if p.facility is not None
    ]
    themes = [
        GapRow(
            key=f"c-{t.category.pk}",
            name=t.category.name,
            category=t.category,
            facility=None,
            wish=t.citizen_share,
            spend=t.spend_share,
            mine=t.mine,
        )
        for t in overview.themes
    ]
    return Results(
        places=sorted(places, key=lambda r: (-r.gap, r.name)),
        themes=sorted(themes, key=lambda r: (-r.gap, r.name)),
        fiscal_year=overview.fiscal_year,
        total_points=overview.total_points,
    )


def _spend_by_facility(fiscal_year: int | None) -> dict[int, Decimal]:
    if fiscal_year is None:
        return {}
    rows = (
        Expenditure.objects.filter(kind=ExpenditureKind.ACTUAL, fiscal_year=fiscal_year)
        .values("facility_id")
        .annotate(total=Sum("amount"))
    )
    return {row["facility_id"]: row["total"] for row in rows}
