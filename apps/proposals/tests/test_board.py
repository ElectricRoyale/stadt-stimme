import pytest
from django.test import override_settings

from apps.access.models import Participant
from apps.catalog.models import Measure
from apps.proposals.admin import stamp_dates
from apps.proposals.board import Stage, build_board
from apps.proposals.models import Proposal, ProposalStatus, Support
from apps.proposals.services import similar_measures
from apps.proposals.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


def _proposal(catalog: Catalog, status: str = ProposalStatus.OPEN, **fields: object) -> Proposal:
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
    rejected = _proposal(catalog, ProposalStatus.REJECTED)

    board = build_board(None)
    stages = {i.proposal.pk: i.stage for i in board.items}

    assert stages[collecting.pk] == Stage.COLLECTING
    assert stages[review.pk] == Stage.REVIEW
    assert stages[accepted.pk] == Stage.ACCEPTED
    assert board.counts == {
        "sammelt": 1,
        "pruefung": 1,
        "angenommen": 1,
        "abgelehnt": 1,
    }
    assert len(board.visible) == 4
    rejected_item = next(i for i in board.items if i.proposal.pk == rejected.pk)
    assert rejected_item.marks == ("done", "done", "done", "no")
    assert rejected_item.sentence == "Abgelehnt, 0 Unterstützungen."


@override_settings(PROPOSAL_SUPPORT_THRESHOLD=2, PROPOSALS_PER_DAY=5)
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

    assert mine.proposal == own and board.visible[0] == mine
    assert mine.stage == Stage.COLLECTING
    assert mine.sentence == "0 von 2 Unterstützungen, noch 2 bis zur Prüfung."
    assert item.supported and board.supported == [item]
    assert item.sentence == "2 Unterstützungen. Die Verwaltung prüft seit 0 Tagen."
    assert item.can_support and not mine.can_support
    assert board.left_today == 4


def test_admin_decision_date_is_set_once(catalog: Catalog) -> None:
    proposal = _proposal(catalog)
    stamp_dates(proposal)
    assert proposal.decided_at is None

    proposal.status = ProposalStatus.ACCEPTED
    stamp_dates(proposal)
    decided = proposal.decided_at
    stamp_dates(proposal)

    assert decided is not None and proposal.decided_at == decided


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
