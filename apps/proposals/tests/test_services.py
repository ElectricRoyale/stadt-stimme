from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.access.models import Participant
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import (
    DailyLimitError,
    leading_proposals,
    pending_proposal,
    similar_proposals,
    submit_proposal,
    toggle_support,
)
from apps.proposals.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


def _published(catalog: Catalog, title: str) -> Proposal:
    return Proposal.objects.create(
        participant=new_person(),
        title=title,
        category=catalog.sport,
        status=ProposalStatus.PUBLISHED,
    )


def test_submit_strips_and_starts_unpublished(participant: Participant, catalog: Catalog) -> None:
    proposal = submit_proposal(
        participant,
        title="  Abendöffnung im Hallenbad  ",
        text="",
        category=catalog.sport,
        facility=catalog.bad,
    )

    assert proposal.title == "Abendöffnung im Hallenbad"
    assert proposal.status == ProposalStatus.SUBMITTED
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


def test_similar_ranks_by_shared_words_and_hides_unpublished(
    participant: Participant, catalog: Catalog
) -> None:
    best = _published(catalog, "Abendöffnung im Hallenbad")
    other = _published(catalog, "Neue Duschen im Hallenbad")
    _published(catalog, "Mehr Fahrradbügel am Bahnhof")
    Proposal.objects.create(
        participant=new_person(), title="Hallenbad Abendöffnung bitte", category=catalog.sport
    )

    items = similar_proposals("Längere Abendöffnung für das Hallenbad", participant)

    assert [i.proposal for i in items] == [best, other]
    assert similar_proposals("kurz", participant) == []


def test_toggle_support(participant: Participant, catalog: Catalog) -> None:
    proposal = _published(catalog, "Abendöffnung im Hallenbad")

    assert toggle_support(proposal, participant) is True
    assert similar_proposals("Hallenbad", participant)[0].supported is True
    assert toggle_support(proposal, participant) is False
    assert proposal.supports.count() == 0


@override_settings(PROPOSAL_SUPPORT_THRESHOLD=2)
def test_leading_proposals_rank_by_support(participant: Participant, catalog: Catalog) -> None:
    quiet, popular = _published(catalog, "Leise Idee"), _published(catalog, "Beliebte Idee")
    toggle_support(popular, participant)
    toggle_support(popular, new_person())
    toggle_support(quiet, new_person())
    Proposal.objects.create(
        participant=participant, title="Noch in Prüfung", category=catalog.sport
    )

    cards = leading_proposals(participant)

    assert [c.proposal for c in cards] == [popular, quiet]
    assert (cards[0].supports, cards[0].supported, cards[0].reached) == (2, True, True)
    assert (cards[1].progress, cards[1].supported, cards[1].own) == (50, False, False)
    assert leading_proposals(None)[0].supported is False


@override_settings(PROPOSAL_REVIEW_DAYS=14)
def test_pending_proposal_has_review_deadline(participant: Participant, catalog: Catalog) -> None:
    assert pending_proposal(participant) is None
    assert pending_proposal(None) is None
    proposal = Proposal.objects.create(
        participant=participant, title="Zebrastreifen an der Schule", category=catalog.sport
    )

    pending = pending_proposal(participant)

    assert pending is not None
    assert pending.proposal == proposal
    assert pending.decision_by == timezone.localdate() + timedelta(days=14)
    assert pending.days_left == 14
