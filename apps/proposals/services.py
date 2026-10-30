"""Fachlogik für Vorschläge: einreichen mit Tageslimit, Ähnliche finden, unterstützen."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Category, Facility, Measure, MeasureStatus
from apps.proposals.models import Proposal, ProposalStatus, Support

SIMILAR_LIMIT = 3
_MIN_WORD_LENGTH = 5
_STEM_LENGTH = 5  # Hallenbad/Hallenbades, Abend/abends: gleiche ersten fünf Buchstaben
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
    point: tuple[Decimal, Decimal] | None = None,
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
            latitude=point[0] if point else None,
            longitude=point[1] if point else None,
        )


def keywords(text: str) -> set[str]:
    """Wortstämme der längeren Wörter: die ersten fünf Buchstaben."""
    words = _WORD.findall(text.lower())
    return {w[:_STEM_LENGTH] for w in words if len(w) >= _MIN_WORD_LENGTH}


def _title_matches(words: set[str]) -> Q:
    matches = Q()
    for word in words:
        matches |= Q(title__icontains=word)
    return matches


def similar_measures(text: str) -> list[Measure]:
    """Geplante oder laufende Maßnahmen mit denselben Wortstämmen im Titel."""
    words = keywords(text)
    if not words:
        return []
    candidates = Measure.objects.filter(_title_matches(words)).exclude(
        status__in=[MeasureStatus.REJECTED, MeasureStatus.COMPLETED]
    )
    ranked = sorted(
        candidates.select_related("facility")[:50],
        key=lambda m: (-len(words & keywords(m.title)), m.title),
    )
    return ranked[:SIMILAR_LIMIT]


def similar_proposals(text: str, viewer: Participant | None) -> list[SimilarProposal]:
    """Öffentliche Vorschläge, deren Titel die meisten Wortstämme des Textes enthalten."""
    words = keywords(text)
    if not words:
        return []
    candidates = (
        Proposal.objects.filter(
            _title_matches(words),
            status__in=[ProposalStatus.OPEN, ProposalStatus.ACCEPTED],
        )
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


def place_from_proposal(proposal: Proposal) -> Facility | None:
    """Ein angenommener Vorschlag mit neuem Ort wird eine eigene Einrichtung (ADR-024).

    So steht der Ort in „Punkte verteilen“ als eigene Zeile, auf den Karten und in den
    Ergebnissen. Der Punkt wandert an die Einrichtung; der Vorschlag zeigt danach auf sie.
    """
    if proposal.facility_id is not None or not proposal.has_point:
        return None
    with transaction.atomic():
        facility = Facility.objects.create(
            external_id=f"VORSCHLAG-{proposal.pk}",
            name=proposal.title,
            category=proposal.category,
            description=proposal.text or f"Neuer Ort aus Vorschlag {proposal.number}.",
            latitude=proposal.latitude,
            longitude=proposal.longitude,
        )
        proposal.facility = facility
        proposal.latitude = proposal.longitude = None
        proposal.save(update_fields=["facility", "latitude", "longitude"])
    return facility


def after_accept(proposal: Proposal) -> None:
    """Folgen des Annehmens, egal ob über Verwaltungsseite oder Admin.

    Neuer Ort wird eine Einrichtung (ADR-024); eine erledigte Einrichtung ist wieder wählbar,
    weil Bürger dort erneut einen Wunsch haben (ADR-029).
    """
    place_from_proposal(proposal)
    if proposal.facility is not None and proposal.facility.is_done:
        proposal.facility.reopen()


ANSWER_MIN_LENGTH = 20


class DecisionError(Exception):
    pass


def decide_proposal(
    proposal: Proposal, *, accept: bool, answer: str, measure: Measure | None = None
) -> Proposal:
    """Annehmen oder ablehnen, mit öffentlicher Antwort (ADR-016, ADR-026).

    Nur offene Vorschläge; ein angenommener neuer Ort wird eine Einrichtung (ADR-024).
    """
    answer = answer.strip()
    if proposal.status != ProposalStatus.OPEN:
        raise DecisionError("Dieser Vorschlag ist schon entschieden.")
    if len(answer) < ANSWER_MIN_LENGTH:
        raise DecisionError(f"Die Antwort braucht mindestens {ANSWER_MIN_LENGTH} Zeichen.")
    with transaction.atomic():
        proposal.status = ProposalStatus.ACCEPTED if accept else ProposalStatus.REJECTED
        proposal.answer = answer
        proposal.measure = measure if accept else None
        proposal.decided_at = timezone.now()
        proposal.save(update_fields=["status", "answer", "measure", "decided_at"])
        if accept:
            after_accept(proposal)
    return proposal
