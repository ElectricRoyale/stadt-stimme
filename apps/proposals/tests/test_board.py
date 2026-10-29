from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Measure
from apps.proposals.admin import stamp_dates
from apps.proposals.board import Stage, build_board
from apps.proposals.models import Proposal, ProposalStatus, Support
from apps.proposals.services import similar_measures
from apps.proposals.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


def _proposal(
    catalog: Catalog, status: str = ProposalStatus.PUBLISHED, **fields: object
) -> Proposal:
    fields.setdefault(
        "published_at", timezone.now() if status != ProposalStatus.SUBMITTED else None
    )
    return Proposal.objects.create(
        participant=new_person(),
        title="Abendöffnung im Hallenbad",
        category=catalog.sport,
        status=status,
        **fields,
    )


def _support(proposal: Proposal, n: int) -> None:
    for _ in range(n):
        Support.objects.create(proposal=proposal, participant=new_person())


@override_settings(PROPOSAL_SUPPORT_THRESHOLD=2)
def test_stage_follows_status_and_threshold(catalog: Catalog) -> None:
    collecting = _proposal(catalog)
    review = _proposal(catalog)
    _support(collecting, 1)
    _support(review, 2)
    accepted = _proposal(catalog, ProposalStatus.ACCEPTED)
    early = _proposal(catalog, ProposalStatus.REJECTED, published_at=None)
    _proposal(catalog, ProposalStatus.SUBMITTED)

    board = build_board(None)
    stages = {i.proposal.pk: i.stage for i in board.items}

    assert stages[collecting.pk] == Stage.COLLECTING
    assert stages[review.pk] == Stage.REVIEW
    assert stages[accepted.pk] == Stage.ACCEPTED
    assert board.counts == {
        "eingereicht": 1,
        "sammelt": 1,
        "pruefung": 1,
        "angenommen": 1,
        "abgelehnt": 1,
    }
    assert board.refused_early == 1
    assert {i.proposal.pk for i in board.visible} == {collecting.pk, review.pk, accepted.pk}
    early_item = next(i for i in board.items if i.proposal.pk == early.pk)
    assert early_item.marks == ("no", "todo", "todo", "todo")
    assert early_item.sentence == "Nicht freigegeben."


@override_settings(PROPOSAL_SUPPORT_THRESHOLD=2, PROPOSAL_REVIEW_DAYS=14, PROPOSALS_PER_DAY=5)
def test_own_proposals_and_sentences(participant: Participant, catalog: Catalog) -> None:
    own = Proposal.objects.create(
        participant=participant, title="Mehr Bänke im Park", category=catalog.sport
    )
    review = _proposal(catalog)
    _support(review, 1)
    Support.objects.create(proposal=review, participant=participant)

    board = build_board(participant)
    mine = board.mine[0]
    item = next(i for i in board.items if i.proposal.pk == review.pk)

    assert mine.proposal == own and mine.visible and board.visible[0] == mine
    assert mine.sentence.startswith("Wartet auf Freigabe durch die Stadt, noch 14 Tage.")
    assert item.supported and board.supported == [item]
    assert item.sentence == "2 Unterstützungen. Die Verwaltung prüft seit 0 Tagen."
    assert item.can_support and not mine.can_support
    assert board.left_today == 4


def test_admin_dates_are_set_once(catalog: Catalog) -> None:
    proposal = _proposal(catalog, ProposalStatus.SUBMITTED)
    proposal.status = ProposalStatus.PUBLISHED
    stamp_dates(proposal)
    published = proposal.published_at
    proposal.status = ProposalStatus.ACCEPTED
    stamp_dates(proposal)

    assert published is not None
    assert proposal.published_at == published
    assert proposal.decided_at is not None and proposal.decided_at >= published - timedelta(
        seconds=1
    )


def test_similar_measures_by_word_stem(catalog: Catalog) -> None:
    Measure.objects.create(
        external_id="M-1",
        facility=catalog.bad,
        title="Längere Öffnungszeiten am Abend",
        status="beschlossen",
    )
    Measure.objects.create(
        external_id="M-2", facility=catalog.bad, title="Abendkurse beendet", status="abgeschlossen"
    )

    found = similar_measures("Hallenbad abends länger offen")

    assert [m.title for m in found] == ["Längere Öffnungszeiten am Abend"]
