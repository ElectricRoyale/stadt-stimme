"""Ergebnisse „Wunsch und Haushalt“: Lücke je Einrichtung und je Thema (ADR-006, ADR-013).

Die Lücke ist der Anteil an allen Bürgerpunkten minus der Anteil an den Ist-Ausgaben des letzten
abgeschlossenen Haushaltsjahres, in Prozentpunkten. Positiv heißt: Bürgern ist es wichtiger, als
es im Haushalt abgebildet ist.
"""

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from apps.catalog.models import Category, Facility
from apps.catalog.spending import actual_spend_by_facility
from apps.points.overview import format_eur
from apps.reporting.statistics import Overview, share

GapTone = Literal["citizens", "city", "even"]


def format_int(value: int) -> str:
    """Ganze Zahl mit Tausenderpunkt: 97.200."""
    return f"{value:,}".replace(",", ".")


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
    points: int = 0
    spend_amount: Decimal = Decimal(0)
    general_points: int = 0  # nur Themen: Punkte für „… allgemein“

    @property
    def is_theme(self) -> bool:
        return self.facility is None

    @property
    def share_scale(self) -> int:
        """Achse der beiden Anteilsbalken im Detail: nächster Zehner über dem größeren Anteil."""
        return min(100, (max(self.wish, self.spend) // 10 + 1) * 10)

    @property
    def points_text(self) -> str:
        return format_int(self.points)

    @property
    def spend_text(self) -> str:
        return format_eur(self.spend_amount)

    @property
    def gap(self) -> int:
        return self.wish - self.spend

    @property
    def gap_size(self) -> int:
        """Betrag der Lücke, für Balkenbreite und Kartenquadrat."""
        return abs(self.gap)

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
            return "Den Bürgerinnen und Bürgern ist das wichtiger, als es der Haushalt abbildet."
        if self.gap < 0:
            return (
                "Hierhin fließt ein größerer Teil des Geldes, "
                "als es dem Anteil der Bürgerpunkte entspricht."
            )
        return "Wunsch und Haushalt liegen gleichauf."


@dataclass(frozen=True)
class Results:
    places: list[GapRow]
    themes: list[GapRow]
    fiscal_year: int | None
    total_points: int
    spend_total: Decimal = Decimal(0)
    participants: int = 0
    average_points: int = 0

    @property
    def rows(self) -> list[GapRow]:
        return self.places + self.themes

    @property
    def gap_scale(self) -> int:
        """Eine Achse für alle Lückenbalken, auf zehn Prozentpunkte aufgerundet."""
        widest = max((abs(r.gap) for r in self.rows), default=0)
        return max(10, math.ceil(widest / 10) * 10)

    @property
    def lead(self) -> GapRow | None:
        """Ort, an dem Bürgern am meisten mehr wichtig ist, als die Stadt ausgibt."""
        return next((r for r in self.places if r.gap > 0), None)

    @property
    def city_lead(self) -> GapRow | None:
        """Ort, an dem die Stadt am meisten mehr ausgibt, als gewünscht wird."""
        return next((r for r in reversed(self.places) if r.gap < 0), None)

    @property
    def general_points(self) -> int:
        return sum(t.general_points for t in self.themes)

    @property
    def participants_text(self) -> str:
        return format_int(self.participants)

    @property
    def total_points_text(self) -> str:
        return format_int(self.total_points)

    @property
    def spend_total_text(self) -> str:
        return format_eur(self.spend_total)

    @property
    def general_share(self) -> int:
        return share(self.general_points, self.total_points)

    def select(self, key: str | None) -> GapRow | None:
        """Gewählte Zeile; sonst der Ort mit der größten Lücke."""
        by_key = {r.key: r for r in self.rows}
        if key in by_key:
            return by_key[key]
        return next(iter(self.rows), None)


def build_results(overview: Overview) -> Results:
    spend = actual_spend_by_facility(overview.fiscal_year)
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
            points=p.points,
            spend_amount=spend.get(p.facility.pk, Decimal(0)),
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
            points=sum(p.points for p in overview.places if p.category == t.category),
            spend_amount=t.spend,
            general_points=sum(
                p.points for p in overview.places if p.is_general and p.category == t.category
            ),
        )
        for t in overview.themes
    ]
    return Results(
        places=sorted(places, key=lambda r: (-r.gap, r.name)),
        themes=sorted(themes, key=lambda r: (-r.gap, r.name)),
        fiscal_year=overview.fiscal_year,
        total_points=overview.total_points,
        spend_total=spend_total,
        participants=overview.participants,
        average_points=overview.average_points,
    )
