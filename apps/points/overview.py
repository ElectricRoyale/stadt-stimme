"""Lesemodell für „Punkte verteilen“: Themen mit „… allgemein“ und ihren Einrichtungen.

Jede Zeile nennt die Ist-Ausgaben des letzten abgeschlossenen Haushaltsjahres und ihren Anteil an
allen Ausgaben (ADR-006), damit man die eigenen Punkte neben den Haushalt legen kann.
"""

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Prefetch

from apps.catalog.models import Category, Facility, Measure
from apps.catalog.spending import actual_spend_by_facility
from apps.points.services import Target
from apps.proposals.models import Proposal, ProposalStatus


def format_eur(amount: Decimal) -> str:
    """Ganze Euro mit Tausenderpunkt: 1.480.000 €."""
    return f"{int(amount):,} €".replace(",", ".")


def format_share(value: float) -> str:
    """Prozent mit einer Nachkommastelle und Dezimalkomma: 37,8."""
    return f"{value:.1f}".replace(".", ",")


def sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:]


@dataclass(frozen=True)
class Row:
    """Ein Ziel: eine Einrichtung oder das ganze Thema (``facility`` ist dann None)."""

    target: Target
    name: str
    facility: Facility | None
    spend: Decimal | None
    spend_share: float
    measures: list[Measure]
    points: int
    # Angenommene Vorschläge als Hinweis: am Ort, ohne Ort beim ganzen Thema (ADR-023).
    proposals: list[Proposal] = field(default_factory=list)

    @property
    def is_general(self) -> bool:
        return self.facility is None

    @property
    def address(self) -> str:
        return self.facility.address if self.facility else ""

    @property
    def spend_text(self) -> str:
        """„1.480.000 € (37,8 %)“; ohne Ist-Ausgaben „keine Angaben“."""
        if self.spend is None:
            return "keine Angaben"
        return f"{format_eur(self.spend)} ({format_share(self.spend_share)} %)"


@dataclass(frozen=True)
class Group:
    category: Category
    spend_share: int
    rows: list[Row] = field(default_factory=list)

    @property
    def points(self) -> int:
        return sum(row.points for row in self.rows)

    @property
    def places(self) -> list[Row]:
        return [row for row in self.rows if not row.is_general]


def build_groups(points: Mapping[Target, int], fiscal_year: int | None) -> list[Group]:
    """Ein Thema je Kategorie: zuerst „… allgemein“, dann die Einrichtungen nach Name."""
    spend = actual_spend_by_facility(fiscal_year)
    total = sum(spend.values(), Decimal(0))
    facilities = Prefetch(
        "facilities",
        queryset=Facility.objects.order_by("name").prefetch_related(
            Prefetch("measures", queryset=Measure.objects.order_by("title"))
        ),
    )
    at_place, at_theme = _accepted_proposals()
    groups = []
    for category in Category.objects.order_by("name").prefetch_related(facilities):
        members = list(category.facilities.all())
        if not members:
            continue
        rows = [_facility_row(f, spend.get(f.pk), total, points, at_place[f.pk]) for f in members]
        theme_spend = sum((r.spend or Decimal(0) for r in rows), Decimal(0))
        general = Row(
            target=Target("c", category.pk),
            name=f"{category.name} allgemein",
            facility=None,
            spend=None,
            spend_share=0.0,
            measures=[],
            points=points.get(Target("c", category.pk), 0),
            proposals=at_theme[category.pk],
        )
        groups.append(
            Group(
                category=category,
                spend_share=round(_percent(theme_spend, total)),
                rows=[general, *rows],
            )
        )
    return groups


def _accepted_proposals() -> tuple[dict[int, list[Proposal]], dict[int, list[Proposal]]]:
    """Angenommene Vorschläge nach Einrichtung und, ohne Einrichtung, nach Thema."""
    at_place: dict[int, list[Proposal]] = defaultdict(list)
    at_theme: dict[int, list[Proposal]] = defaultdict(list)
    accepted = Proposal.objects.filter(status=ProposalStatus.ACCEPTED).order_by("-decided_at")
    for proposal in accepted:
        if proposal.facility_id is not None:
            at_place[proposal.facility_id].append(proposal)
        else:
            at_theme[proposal.category_id].append(proposal)
    return at_place, at_theme


def _facility_row(
    facility: Facility,
    spend: Decimal | None,
    total: Decimal,
    points: Mapping[Target, int],
    proposals: list[Proposal],
) -> Row:
    target = Target("f", facility.pk)
    return Row(
        target=target,
        name=facility.name,
        facility=facility,
        spend=spend,
        spend_share=_percent(spend or Decimal(0), total),
        measures=list(facility.measures.all()),
        points=points.get(target, 0),
        proposals=proposals,
    )


def _percent(part: Decimal, total: Decimal) -> float:
    return float(part / total * 100) if total else 0.0


@dataclass(frozen=True)
class Cell:
    """Eines der 100 Quadrate; ``key`` None heißt frei."""

    key: str | None
    general: bool = False
    color: str = ""


def ledger_cells(groups: list[Group], budget: int) -> list[Cell]:
    """Je Thema erst die Einrichtungen, dann „… allgemein“, danach die freien Quadrate."""
    cells: list[Cell] = []
    for group in groups:
        for row in [*group.places, *(r for r in group.rows if r.is_general)]:
            cells += [Cell(row.target.key, row.is_general, group.category.color)] * row.points
    cells = cells[:budget]
    return cells + [Cell(None)] * (budget - len(cells))


def lead_group(groups: list[Group]) -> Group | None:
    """Thema, dem man deutlich mehr Punkte gibt, als es Anteil an den Ausgaben hat."""
    ranked = [g for g in groups if g.points > g.spend_share]
    return max(ranked, key=lambda g: (g.points - g.spend_share, g.points), default=None)


def map_places(groups: list[Group]) -> list[dict[str, object]]:
    """Einrichtungen mit Koordinaten für die Karte; nur Werte, kein HTML (json_script)."""
    return [
        {
            "key": row.target.key,
            "name": row.name,
            "color": group.category.color,
            "lat": float(row.facility.latitude or 0),
            "lng": float(row.facility.longitude or 0),
        }
        for group in groups
        for row in group.places
        if row.facility is not None and row.facility.has_location
    ]
