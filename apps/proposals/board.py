"""Übersicht „Vorschläge“: Schritt jedes Vorschlags, Zähler und die eigene Beteiligung (ADR-016).

Die Schritte folgen aus dem Status und den Unterstützungen:
eingereicht (nur der Autor sieht ihn), sammelt (freigegeben, unter der Schwelle), in Prüfung
(freigegeben, Schwelle erreicht), angenommen, abgelehnt (ohne Freigabe: schon vor der Freigabe).
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from typing import Literal

from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from apps.access.models import Participant
from apps.proposals.models import Proposal, ProposalStatus, Support

Mark = Literal["done", "here", "todo", "yes", "no"]


class Stage(StrEnum):
    SUBMITTED = "eingereicht"
    COLLECTING = "sammelt"
    REVIEW = "pruefung"
    ACCEPTED = "angenommen"
    REJECTED = "abgelehnt"

    @property
    def label(self) -> str:
        return STAGE_LABELS[self]


STAGE_LABELS = {
    Stage.SUBMITTED: "Eingereicht",
    Stage.COLLECTING: "Sammelt Unterstützung",
    Stage.REVIEW: "In Prüfung",
    Stage.ACCEPTED: "Angenommen",
    Stage.REJECTED: "Abgelehnt",
}


def _plural(n: int, one: str, many: str) -> str:
    return one if n == 1 else many


@dataclass(frozen=True)
class Item:
    proposal: Proposal
    supports: int
    supported: bool
    own: bool
    review_since: date | None = None

    @property
    def stage(self) -> Stage:
        status = self.proposal.status
        if status == ProposalStatus.SUBMITTED:
            return Stage.SUBMITTED
        if status == ProposalStatus.ACCEPTED:
            return Stage.ACCEPTED
        if status == ProposalStatus.REJECTED:
            return Stage.REJECTED
        threshold = settings.PROPOSAL_SUPPORT_THRESHOLD
        return Stage.REVIEW if self.supports >= threshold else Stage.COLLECTING

    @property
    def refused_early(self) -> bool:
        return self.stage == Stage.REJECTED and self.proposal.published_at is None

    @property
    def visible(self) -> bool:
        """Öffentlich erst nach der Freigabe; der Autor sieht seine eigenen immer."""
        return self.own or self.proposal.published_at is not None

    @property
    def can_support(self) -> bool:
        return not self.own and self.stage in (Stage.COLLECTING, Stage.REVIEW)

    @property
    def progress(self) -> int:
        """Strecke zwischen „Sammelt“ und „In Prüfung“: Unterstützungen zur Schwelle, in Prozent."""
        if self.stage == Stage.SUBMITTED or self.refused_early:
            return 0
        threshold = settings.PROPOSAL_SUPPORT_THRESHOLD
        return min(100, round(self.supports / threshold * 100)) if threshold else 100

    @property
    def marks(self) -> tuple[Mark, Mark, Mark, Mark]:
        """Die vier Stationen: eingereicht, sammelt, in Prüfung, entschieden."""
        stage = self.stage
        if stage == Stage.SUBMITTED:
            return ("here", "todo", "todo", "todo")
        if stage == Stage.COLLECTING:
            return ("done", "here", "todo", "todo")
        if stage == Stage.REVIEW:
            return ("done", "done", "here", "todo")
        if stage == Stage.ACCEPTED:
            return ("done", "done", "done", "yes")
        if self.refused_early:
            return ("no", "todo", "todo", "todo")
        return ("done", "done", "done", "no")

    @property
    def release_days_left(self) -> int:
        submitted = timezone.localdate(self.proposal.created_at)
        deadline = submitted + timedelta(days=settings.PROPOSAL_REVIEW_DAYS)
        return max(0, (deadline - timezone.localdate()).days)

    @property
    def sentence(self) -> str:
        threshold = settings.PROPOSAL_SUPPORT_THRESHOLD
        n = self.supports
        stage = self.stage
        if stage == Stage.SUBMITTED:
            days = self.release_days_left
            return (
                f"Wartet auf Freigabe durch die Stadt, noch {days} {_plural(days, 'Tag', 'Tage')}. "
                "Bis dahin siehst nur du ihn."
            )
        if stage == Stage.COLLECTING:
            return f"{n} von {threshold} Unterstützungen, noch {threshold - n} bis zur Prüfung."
        if stage == Stage.REVIEW:
            days = (timezone.localdate() - self.review_since).days if self.review_since else 0
            return (
                f"{n} {_plural(n, 'Unterstützung', 'Unterstützungen')}. "
                f"Die Verwaltung prüft seit {days} {_plural(days, 'Tag', 'Tagen')}."
            )
        if stage == Stage.ACCEPTED:
            return f"Mit {n} {_plural(n, 'Unterstützung', 'Unterstützungen')} angenommen."
        if self.refused_early:
            return "Nicht freigegeben."
        return f"Nach Prüfung abgelehnt, {n} {_plural(n, 'Unterstützung', 'Unterstützungen')}."

    @property
    def search_text(self) -> str:
        p = self.proposal
        return f"{p.title} {p.text} {p.facility.name if p.facility else ''} {p.number}".lower()


@dataclass(frozen=True)
class Board:
    items: list[Item]
    left_today: int

    @property
    def visible(self) -> list[Item]:
        """Eigene zuerst, sonst nach Unterstützung."""
        shown = [i for i in self.items if i.visible]
        return sorted(shown, key=lambda i: (not i.own, -i.supports, -i.proposal.pk))

    def count(self, stage: Stage) -> int:
        return sum(1 for i in self.items if i.stage == stage)

    @property
    def counts(self) -> dict[str, int]:
        """Zähler je Schritt, für Vorlagen nach Wert: ``board.counts.sammelt``."""
        return {stage.value: self.count(stage) for stage in Stage}

    @property
    def submitted_of_others(self) -> int:
        return sum(1 for i in self.items if i.stage == Stage.SUBMITTED and not i.own)

    @property
    def accepted_as_measure(self) -> int:
        return sum(1 for i in self.items if i.stage == Stage.ACCEPTED and i.proposal.measure_id)

    @property
    def refused_early(self) -> int:
        return sum(1 for i in self.items if i.refused_early)

    def leading(self, limit: int = 3) -> list[Item]:
        """Fremde Vorschläge, die man noch unterstützen kann, die meisten Unterstützungen zuerst."""
        open_items = [i for i in self.items if i.can_support and i.visible]
        return sorted(open_items, key=lambda i: (-i.supports, -i.proposal.pk))[:limit]

    @property
    def latest_own(self) -> Item | None:
        """Neuester eigener Vorschlag, solange er noch nicht entschieden ist."""
        undecided = (Stage.SUBMITTED, Stage.COLLECTING, Stage.REVIEW)
        return next((i for i in self.mine if i.stage in undecided), None)

    @property
    def mine(self) -> list[Item]:
        return [i for i in self.items if i.own]

    @property
    def supported(self) -> list[Item]:
        return [i for i in self.items if i.supported and i.visible]


def build_board(viewer: Participant | None) -> Board:
    proposals = list(
        Proposal.objects.select_related("category", "facility", "measure")
        .annotate(support_count=Count("supports"))
        .order_by("-created_at")
    )
    mine = _supported_ids(viewer)
    review = _review_since([p for p in proposals if p.support_count > 0])
    items = [
        Item(
            proposal=p,
            supports=p.support_count,
            supported=p.pk in mine,
            own=viewer is not None and p.participant_id == viewer.pk,
            review_since=review.get(p.pk),
        )
        for p in proposals
    ]
    return Board(items=items, left_today=proposals_left_today(viewer))


def item_for(proposal: Proposal, viewer: Participant | None) -> Item:
    """Ein einzelner Vorschlag im selben Zuschnitt, etwa nach dem Unterstützen."""
    supports = proposal.supports.count()
    return Item(
        proposal=proposal,
        supports=supports,
        supported=viewer is not None and proposal.supports.filter(participant=viewer).exists(),
        own=viewer is not None and proposal.participant_id == viewer.pk,
        review_since=_review_since([proposal]).get(proposal.pk),
    )


def proposals_left_today(viewer: Participant | None) -> int:
    if viewer is None:
        return 0
    since = timezone.now() - timedelta(days=1)
    used = Proposal.objects.filter(participant=viewer, created_at__gte=since).count()
    return max(0, settings.PROPOSALS_PER_DAY - used)


def _supported_ids(viewer: Participant | None) -> set[int]:
    if viewer is None:
        return set()
    return set(Support.objects.filter(participant=viewer).values_list("proposal_id", flat=True))


def _review_since(proposals: list[Proposal]) -> dict[int, date]:
    """Tag, an dem die Schwelle erreicht wurde: Zeitpunkt der N-ten Unterstützung."""
    threshold = settings.PROPOSAL_SUPPORT_THRESHOLD
    rows = (
        Support.objects.filter(proposal__in=proposals)
        .order_by("proposal_id", "created_at")
        .values_list("proposal_id", "created_at")
    )
    seen: dict[int, int] = defaultdict(int)
    reached: dict[int, date] = {}
    for proposal_id, created_at in rows:
        seen[proposal_id] += 1
        if seen[proposal_id] == max(threshold, 1):
            reached[proposal_id] = timezone.localdate(created_at)
    return reached
