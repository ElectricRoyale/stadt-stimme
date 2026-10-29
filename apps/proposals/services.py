"""Fachlogik für Vorschläge: einreichen mit Tageslimit, Ähnliche finden, unterstützen."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Category, Facility
from apps.proposals.models import Proposal, ProposalStatus, Support

SIMILAR_LIMIT = 2
_MIN_WORD_LENGTH = 5
_WORD = re.compile(r"\w+")


class DailyLimitError(Exception):
    def __init__(self) -> None:
        super().__init__(
            f"Du kannst höchstens {settings.PROPOSALS_PER_DAY} Vorschläge am Tag einreichen."
        )


@dataclass(frozen=True)
class SimilarProposal:
    proposal: Proposal
    supports: int
    supported: bool


def submit_proposal(
    participant: Participant,
    *,
    title: str,
    text: str,
    category: Category,
    facility: Facility | None,
) -> Proposal:
    with transaction.atomic():
        # Zeile sperren, damit parallele Anfragen das Tageslimit nicht umgehen.
        Participant.objects.select_for_update().get(pk=participant.pk)
        since = timezone.now() - timedelta(days=1)
        recent = Proposal.objects.filter(participant=participant, created_at__gte=since)
        if recent.count() >= settings.PROPOSALS_PER_DAY:
            raise DailyLimitError
        return Proposal.objects.create(
            participant=participant,
            title=title.strip(),
            text=text.strip(),
            category=category,
            facility=facility,
        )


def keywords(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if len(w) >= _MIN_WORD_LENGTH}


def similar_proposals(text: str, viewer: Participant | None) -> list[SimilarProposal]:
    """Freigegebene Vorschläge, deren Titel die meisten längeren Wörter des Textes enthalten."""
    words = keywords(text)
    if not words:
        return []
    matches = Q()
    for word in words:
        matches |= Q(title__icontains=word)
    candidates = (
        Proposal.objects.filter(matches, status=ProposalStatus.PUBLISHED)
        .annotate(support_count=Count("supports"))
        .order_by("-created_at")[:50]
    )
    ranked = sorted(candidates, key=lambda p: (-len(words & keywords(p.title)), -p.support_count))[
        :SIMILAR_LIMIT
    ]
    mine = _supported_by(viewer, ranked)
    return [SimilarProposal(p, p.support_count, p.pk in mine) for p in ranked]


def toggle_support(proposal: Proposal, participant: Participant) -> bool:
    """Unterstützt oder zieht zurück; gibt den neuen Stand zurück."""
    deleted, _ = Support.objects.filter(proposal=proposal, participant=participant).delete()
    if deleted:
        return False
    Support.objects.get_or_create(proposal=proposal, participant=participant)
    return True


def _supported_by(viewer: Participant | None, proposals: Sequence[Proposal]) -> set[int]:
    if viewer is None:
        return set()
    rows = Support.objects.filter(participant=viewer, proposal__in=proposals)
    return set(rows.values_list("proposal_id", flat=True))
