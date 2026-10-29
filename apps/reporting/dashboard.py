"""Lesemodell für die Übersicht im Design „Mannheim“ (ADR-015).

Baut nur auf vorhandenen Daten auf: Kennzahlen aus ``statistics``, Lücken je Einrichtung aus
``results``, eingelöste Codes und geänderte Maßnahmen. Keine eigenen Berechnungen von Anteilen.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from django.db.models import Count, Min
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.access.models import AccessCode
from apps.catalog.models import Category, Measure
from apps.points.models import POINTS_BUDGET
from apps.reporting.results import GapRow, Results, signed
from apps.reporting.statistics import Overview, PlaceStat, ThemeStat

AXIS_STEP = 20
LABEL_FLIP_AT = 0.55  # ab diesem Anteil der Achse rückt die Beschriftung nach links
PARTICIPATION_WEEKS = 8
FEED_ROWS = 3


@dataclass(frozen=True)
class ThemeLine:
    """Eine Zeile „Wunsch und Haushalt“: Thema mit seinen Einrichtungen und „… allgemein“."""

    theme: ThemeStat
    places: list[GapRow]
    general: PlaceStat | None
    is_lead: bool
    axis_max: int

    @property
    def gap_text(self) -> str:
        return signed(self.theme.gap)

    @property
    def label_position(self) -> str:
        """Wo die Beschriftung steht, damit sie in der Spur bleibt und lesbar ist.

        ``after``: rechts der weitesten Marke. Liegt die Marke weit rechts, entweder ``inside``
        (weiß am Ende des roten Balkens) oder ``between`` (zwischen Balken und goldener Marke).
        """
        wish, spend = self.theme.citizen_share, self.theme.spend_share
        if max(wish, spend) <= self.axis_max * LABEL_FLIP_AT:
            return "after"
        return "inside" if wish >= spend else "between"


@dataclass(frozen=True)
class WishBudget:
    lines: list[ThemeLine]
    axis_max: int

    @property
    def ticks(self) -> list[int]:
        return list(range(0, self.axis_max + 1, AXIS_STEP))


def wish_budget(overview: Overview, results: Results) -> WishBudget:
    """Themen nach Lücke absteigend; die größte Lücke steht oben und ist markiert."""
    lead = overview.biggest_gap
    largest = max((max(t.citizen_share, t.spend_share) for t in overview.themes), default=0)
    axis_max = _round_up(largest, AXIS_STEP)
    lines = [
        ThemeLine(
            theme=theme,
            places=[r for r in results.places if r.category == theme.category],
            general=next(
                (p for p in overview.places if p.is_general and p.category == theme.category),
                None,
            ),
            is_lead=theme == lead,
            axis_max=axis_max,
        )
        for theme in sorted(overview.themes, key=lambda t: (-t.gap, t.category.name))
    ]
    return WishBudget(lines=lines, axis_max=axis_max)


def _round_up(value: int, step: int) -> int:
    return max(step, math.ceil(value / step) * step)


@dataclass(frozen=True)
class PointCell:
    """Eines der 100 Quadrate: Thema (None = frei), seine Farbe und ob es ans ganze Thema ging."""

    category_pk: int | None
    general: bool = False
    color: str = ""


@dataclass(frozen=True)
class GivenTheme:
    category: Category
    total: int
    names: list[str]


@dataclass(frozen=True)
class MyPoints:
    cells: list[PointCell]
    themes: list[GivenTheme]
    used: int

    @property
    def free(self) -> int:
        return POINTS_BUDGET - self.used


def my_points(overview: Overview) -> MyPoints:
    """Eigene Punkte als 10 mal 10 Quadrate: je Thema erst Einrichtungen, dann „… allgemein“."""
    cells: list[PointCell] = []
    themes: list[GivenTheme] = []
    for theme in overview.themes:
        own = [p for p in overview.places if p.category == theme.category and p.mine > 0]
        if not own:
            continue
        places = [p for p in own if not p.is_general]
        general = [p for p in own if p.is_general]
        for place in places + general:
            cell = PointCell(theme.category.pk, place.is_general, theme.category.color)
            cells += [cell] * place.mine
        themes.append(
            GivenTheme(
                category=theme.category,
                total=sum(p.mine for p in own),
                names=[p.name for p in places] + [p.name for p in general],
            )
        )
    cells = cells[:POINTS_BUDGET]
    cells += [PointCell(None)] * (POINTS_BUDGET - len(cells))
    return MyPoints(cells=cells, themes=themes, used=overview.mine_used)


@dataclass(frozen=True)
class WeekCount:
    start: date
    count: int
    is_current: bool

    @property
    def week(self) -> int:
        return self.start.isocalendar().week


@dataclass(frozen=True)
class Participation:
    """Eingelöste Codes je Kalenderwoche; die laufende Woche steht zuletzt."""

    weeks: list[WeekCount]

    @property
    def top(self) -> int:
        return nice_top(max((w.count for w in self.weeks), default=0))

    @property
    def middle(self) -> int:
        return self.top // 2

    @property
    def current(self) -> WeekCount:
        return self.weeks[-1]

    def height(self, week: WeekCount) -> float:
        """Balkenhöhe in Prozent der Achse."""
        return round(week.count / self.top * 100, 1)

    @property
    def bars(self) -> list[tuple[WeekCount, float]]:
        return [(w, self.height(w)) for w in self.weeks]


def participation_since() -> date | None:
    """Tag der ersten Einlösung eines Codes, in der Zeitzone der Anwendung."""
    first = AccessCode.objects.aggregate(first=Min("redeemed_at"))["first"]
    return timezone.localdate(first) if first else None


def participation_by_week(
    weeks: int = PARTICIPATION_WEEKS, today: date | None = None
) -> Participation:
    """Montag bis Sonntag, Zeitzone der Anwendung; Wochen ohne Einlösung zählen mit 0."""
    today = today or timezone.localdate()
    current = today - timedelta(days=today.weekday())
    starts = [current - timedelta(weeks=n) for n in range(weeks - 1, -1, -1)]
    rows = (
        AccessCode.objects.filter(redeemed_at__date__gte=starts[0])
        .annotate(day=TruncDate("redeemed_at"))
        .values("day")
        .annotate(total=Count("pk"))
    )
    counts = dict.fromkeys(starts, 0)
    for row in rows:
        day: date = row["day"]
        monday = day - timedelta(days=day.weekday())
        if monday in counts:
            counts[monday] += row["total"]
    return Participation([WeekCount(start, counts[start], start == current) for start in starts])


def nice_top(value: int) -> int:
    """Obere Achsengrenze: Höchstwert aufgerundet auf die erste Stelle (213 → 300), mindestens 4."""
    if value <= 4:
        return 4
    magnitude = 10 ** math.floor(math.log10(value))
    return int(math.ceil(value / magnitude) * magnitude)


@dataclass(frozen=True)
class NewsItem:
    measure: Measure
    mine: int  # eigene Punkte an der Einrichtung der Maßnahme


def recent_measures(mine: Mapping[int, int] | None) -> list[NewsItem]:
    """Zuletzt geänderte Maßnahmen; mit ``mine`` (Einrichtung → eigene Punkte) nur dort."""
    measures = Measure.objects.select_related("facility", "facility__category")
    if mine is not None:
        measures = measures.filter(facility_id__in=list(mine))
    latest = measures.order_by("-updated_at", "title")[:FEED_ROWS]
    return [NewsItem(m, (mine or {}).get(m.facility_id, 0)) for m in latest]
