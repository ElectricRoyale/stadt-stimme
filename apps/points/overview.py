"""Lesemodell für „Punkte verteilen“: Themen mit „… allgemein“ und ihren Einrichtungen."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Prefetch
from django.utils import timezone

from apps.catalog.models import (
    Category,
    Expenditure,
    ExpenditureKind,
    Facility,
    Measure,
    MeasureStatus,
)
from apps.points.services import Target

# Statusfarbe der Design-Tokens (--ss-status-<ton>-bg/-fg) je Maßnahmenstatus.
STATUS_TONE: dict[str, str] = {
    MeasureStatus.OPEN: "idea",
    MeasureStatus.DECIDED: "plan",
    MeasureStatus.IN_PROGRESS: "done",
    MeasureStatus.COMPLETED: "done",
    MeasureStatus.REJECTED: "idea",
}
ACTUAL_YEARS = 3


def format_eur(amount: Decimal) -> str:
    if amount >= 1_000_000:
        millions = f"{amount / 1_000_000:.1f}".replace(".", ",")
        return f"{millions} Mio. €"
    return f"{int(amount):,} €".replace(",", ".")


@dataclass(frozen=True)
class Spending:
    """Ist-Ausgaben der letzten Jahre und Plan für das nächste Haushaltsjahr (ADR-006)."""

    actual: Decimal | None
    actual_label: str
    planned: Decimal | None
    planned_label: str

    @classmethod
    def of(cls, expenditures: Iterable[Expenditure]) -> "Spending":
        year = timezone.localdate().year
        items = list(expenditures)
        actual = [
            e
            for e in items
            if e.kind == ExpenditureKind.ACTUAL and year - ACTUAL_YEARS <= e.fiscal_year < year
        ]
        plans = [e for e in items if e.kind == ExpenditureKind.PLAN and e.fiscal_year >= year]
        plan_year = min((e.fiscal_year for e in plans), default=None)
        planned = [e for e in plans if e.fiscal_year == plan_year]
        return cls(
            actual=sum((e.amount for e in actual), Decimal(0)) if actual else None,
            actual_label=_years_label(e.fiscal_year for e in actual),
            planned=sum((e.amount for e in planned), Decimal(0)) if planned else None,
            planned_label=f"Geplant {plan_year}" if plan_year else "Geplant",
        )

    @property
    def actual_text(self) -> str:
        return format_eur(self.actual) if self.actual is not None else "keine Angaben"

    @property
    def planned_text(self) -> str:
        return format_eur(self.planned) if self.planned is not None else "keine Angaben"


def _years_label(years: Iterable[int]) -> str:
    found = sorted(set(years))
    if not found:
        return "Ausgaben"
    if len(found) == 1:
        return f"Ausgaben {found[0]}"
    return f"Ausgaben {found[0]}\u2013{found[-1]}"


@dataclass(frozen=True)
class ListEntry:
    title: str
    status: str
    tone: str


@dataclass(frozen=True)
class Row:
    target: Target
    name: str
    subtitle: str
    description: str
    is_general: bool
    spending: Spending
    list_title: str
    entries: list[ListEntry]
    points: int


@dataclass(frozen=True)
class Group:
    category: Category
    rows: list[Row] = field(default_factory=list)

    @property
    def points(self) -> int:
        return sum(row.points for row in self.rows)


def build_groups(points: Mapping[Target, int]) -> list[Group]:
    """Ein Thema je Kategorie: zuerst „… allgemein“, dann die Einrichtungen."""
    facilities = Prefetch(
        "facilities",
        queryset=Facility.objects.order_by("name").prefetch_related(
            Prefetch("measures", queryset=Measure.objects.order_by("title")),
            "expenditures",
        ),
    )
    groups = []
    for category in Category.objects.order_by("name").prefetch_related(facilities):
        members = list(category.facilities.all())
        if not members:
            continue
        rows = [_general_row(category, members, points)]
        rows += [_facility_row(facility, points) for facility in members]
        groups.append(Group(category=category, rows=rows))
    return groups


def _general_row(category: Category, members: list[Facility], points: Mapping[Target, int]) -> Row:
    target = Target("c", category.pk)
    return Row(
        target=target,
        name=f"{category.name} allgemein",
        subtitle="ganzes Thema, ohne festen Ort",
        description=(
            f"Die Stadt verteilt diese Punkte auf alle Vorhaben im Thema {category.name}, "
            "auch auf neue, die noch kommen. Gut, wenn dir das Thema wichtig ist, "
            "aber kein bestimmter Ort."
        ),
        is_general=True,
        spending=Spending.of(e for facility in members for e in facility.expenditures.all()),
        list_title="Gehört dazu",
        entries=[ListEntry(f.name, "Ort", "idea") for f in members]
        + [ListEntry("Künftige Vorhaben", "offen", "idea")],
        points=points.get(target, 0),
    )


def _facility_row(facility: Facility, points: Mapping[Target, int]) -> Row:
    target = Target("f", facility.pk)
    return Row(
        target=target,
        name=facility.name,
        subtitle=facility.address,
        description=facility.description,
        is_general=False,
        spending=Spending.of(facility.expenditures.all()),
        list_title="Mögliche Maßnahmen",
        entries=[
            ListEntry(m.title, _sentence_case(m.get_status_display()), STATUS_TONE[m.status])
            for m in facility.measures.all()
        ],
        points=points.get(target, 0),
    )


def _sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:]
