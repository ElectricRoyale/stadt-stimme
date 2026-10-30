import pytest
from django.test import override_settings

from apps.access.models import Participant
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import (
    DailyLimitError,
    similar_proposals,
    submit_proposal,
    toggle_support,
)
from apps.proposals.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


def _open(catalog: Catalog, title: str) -> Proposal:
    return Proposal.objects.create(
        participant=new_person(),
        title=title,
        category=catalog.sport,
        status=ProposalStatus.OPEN,
    )


def test_submit_strips_and_is_open_at_once(participant: Participant, catalog: Catalog) -> None:
    proposal = submit_proposal(
        participant,
        title="  Abendöffnung im Hallenbad  ",
        text="",
        category=catalog.sport,
        facility=catalog.bad,
    )

    assert proposal.title == "Abendöffnung im Hallenbad"
    assert proposal.status == ProposalStatus.OPEN
    assert proposal.number == f"V-{proposal.pk}"


@override_settings(PROPOSALS_PER_DAY=2)
def test_daily_limit(participant: Participant, catalog: Catalog) -> None:
    for _ in range(2):
        submit_proposal(
            participant, title="Mehr Bänke im Park", text="", category=catalog.sport, facility=None
        )

    with pytest.raises(DailyLimitError):
        submit_proposal(
            participant, title="Mehr Bänke im Park", text="", category=catalog.sport, facility=None
        )


def test_similar_ranks_by_shared_words_and_hides_rejected(
    participant: Participant, catalog: Catalog
) -> None:
    best = _open(catalog, "Abendöffnung im Hallenbad")
    other = _open(catalog, "Neue Duschen im Hallenbad")
    _open(catalog, "Mehr Fahrradbügel am Bahnhof")
    Proposal.objects.create(
        participant=new_person(),
        title="Hallenbad Abendöffnung bitte",
        category=catalog.sport,
        status=ProposalStatus.REJECTED,
    )

    items = similar_proposals("Längere Abendöffnung für das Hallenbad", participant)

    assert [i.proposal for i in items] == [best, other]
    assert similar_proposals("kurz", participant) == []


def test_toggle_support(participant: Participant, catalog: Catalog) -> None:
    proposal = _open(catalog, "Abendöffnung im Hallenbad")

    assert toggle_support(proposal, participant) is True
    assert similar_proposals("Hallenbad", participant)[0].supported is True
    assert toggle_support(proposal, participant) is False
    assert proposal.supports.count() == 0
