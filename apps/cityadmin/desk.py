"""Zahlen und Listen der Verwaltungsseite (ADR-026). Nur Summen, keine einzelnen Zugänge."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from apps.access.models import AccessCode, AccessCodeStatus, Participant
from apps.catalog.models import Measure
from apps.proposals.board import Board, Item, Stage
from apps.reporting.results import GapRow, Results


def _days(n: int) -> str:
    return "1 Tag" if abs(n) == 1 else f"{abs(n)} Tage"


@dataclass(frozen=True)
class Task:
    """Ein Vorschlag hat die Schwelle erreicht; die Stadt antwortet binnen der Frist."""

    item: Item
    due: date

    @property
    def days_left(self) -> int:
        return (self.due - timezone.localdate()).days

    @property
    def urgent(self) -> bool:
        return self.days_left <= 2

    @property
    def due_text(self) -> str:
        left = self.days_left
        if left < 0:
            return f"{_days(left)} überfällig"
        return "heute fällig" if left == 0 else f"noch {_days(left)}"


def answer_tasks(board: Board) -> list[Task]:
    """Vorschläge in Prüfung mit Antwortfrist, die früheste zuerst."""
    window = timedelta(days=settings.PROPOSAL_REVIEW_DAYS)
    tasks = [
        Task(item, item.review_since + window)
        for item in board.items
        if item.stage == Stage.REVIEW and item.review_since is not None
    ]
    return sorted(tasks, key=lambda t: (t.due, t.item.proposal.pk))


@dataclass(frozen=True)
class Tab:
    key: str
    label: str
    items: list[Item]
    empty: str


def proposal_tabs(board: Board) -> list[Tab]:
    """In Prüfung zuerst, dann Sammeln, dann Entschieden; neueste oben."""

    def pick(*stages: Stage) -> list[Item]:
        chosen = [i for i in board.items if i.stage in stages]
        return sorted(chosen, key=lambda i: (-i.supports, -i.proposal.pk))

    return [
        Tab(
            "pruefung",
            "In Prüfung",
            pick(Stage.REVIEW),
            "Kein Vorschlag hat die Schwelle erreicht.",
        ),
        Tab("sammelt", "Sammeln", pick(Stage.COLLECTING), "Kein offener Vorschlag sammelt gerade."),
        Tab(
            "entschieden",
            "Entschieden",
            pick(Stage.ACCEPTED, Stage.REJECTED),
            "Noch nichts entschieden.",
        ),
    ]


def selected_tab(tabs: list[Tab], wanted: str) -> Tab:
    """Gewählter Tab; sonst der erste mit Einträgen."""
    by_key = {t.key: t for t in tabs}
    if wanted in by_key:
        return by_key[wanted]
    return next((t for t in tabs if t.items), tabs[0])


@dataclass(frozen=True)
class Batch:
    name: str
    total: int
    redeemed: int
    blocked: int

    @property
    def share(self) -> int:
        return round(self.redeemed / self.total * 100) if self.total else 0


@dataclass(frozen=True)
class Access:
    issued: int
    redeemed: int
    with_points: int
    blocked: int
    batches: list[Batch]

    def _share(self, part: int) -> int:
        return round(part / self.issued * 100) if self.issued else 0

    @property
    def redeemed_share(self) -> int:
        return self._share(self.redeemed)

    @property
    def with_points_share(self) -> int:
        return self._share(self.with_points)


def access_summary() -> Access:
    rows = (
        AccessCode.objects.values("batch")
        .annotate(
            total=Count("pk"),
            redeemed=Count("pk", filter=Q(redeemed_at__isnull=False)),
            blocked=Count("pk", filter=Q(status=AccessCodeStatus.BLOCKED)),
        )
        .order_by("batch")
    )
    batches = [Batch(r["batch"], r["total"], r["redeemed"], r["blocked"]) for r in rows]
    with_points = Participant.objects.filter(allocations__isnull=False).distinct().count()
    return Access(
        issued=sum(b.total for b in batches),
        redeemed=sum(b.redeemed for b in batches),
        with_points=with_points,
        blocked=sum(b.blocked for b in batches),
        batches=batches,
    )


@dataclass(frozen=True)
class LedgerRow:
    gap: GapRow
    measures: list[Measure]


def facility_ledger(results: Results) -> list[LedgerRow]:
    """Einrichtungen nach Lücke (wie in den Ergebnissen), mit ihren Maßnahmen."""
    measures: dict[int, list[Measure]] = defaultdict(list)
    for measure in Measure.objects.order_by("title"):
        measures[measure.facility_id].append(measure)
    return [
        LedgerRow(row, measures[row.facility.pk])
        for row in results.places
        if row.facility is not None
    ]
