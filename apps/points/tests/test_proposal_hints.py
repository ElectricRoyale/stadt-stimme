"""Angenommene Vorschläge als Hinweis beim Punkte verteilen (ADR-023)."""

import re

import pytest
from django.test import Client
from django.utils import timezone

from apps.catalog.models import Facility
from apps.points.tests.conftest import Catalog
from apps.proposals.models import Proposal, ProposalStatus
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db
URL = "/verteilen/"


def _proposal(
    catalog: Catalog,
    title: str,
    facility: Facility | None = None,
    status: str = ProposalStatus.ACCEPTED,
) -> Proposal:
    return Proposal.objects.create(
        participant=new_person(),
        title=title,
        category=catalog.sport,
        facility=facility,
        status=status,
        decided_at=timezone.now(),
    )


def _row(content: str, key: str) -> str:
    match = re.search(rf'<li class="target[^"]*" id="ziel-{key}".*?\n</li>', content, re.S)
    assert match, key
    return match.group(0)


def test_accepted_proposal_shows_at_its_facility(logged_in: Client, catalog: Catalog) -> None:
    proposal = _proposal(catalog, "Längere Öffnungszeiten", facility=catalog.bad)

    content = logged_in.get(URL).content.decode()

    row = _row(content, f"f-{catalog.bad.pk}")
    assert f"Angenommener Vorschlag V-{proposal.pk}:" in row
    assert f'href="/vorschlaege/#vorschlag-{proposal.pk}"' in row


def test_proposal_without_facility_shows_at_theme(logged_in: Client, catalog: Catalog) -> None:
    _proposal(catalog, "Mehr Sportkurse für Ältere")

    content = logged_in.get(URL).content.decode()

    assert "Mehr Sportkurse für Ältere" in _row(content, f"c-{catalog.sport.pk}")
    assert "Mehr Sportkurse für Ältere" not in _row(content, f"f-{catalog.bad.pk}")


def test_only_accepted_proposals_appear(logged_in: Client, catalog: Catalog) -> None:
    _proposal(catalog, "Noch in Prüfung", facility=catalog.bad, status=ProposalStatus.OPEN)

    assert "Noch in Prüfung" not in logged_in.get(URL).content.decode()


def test_proposal_list_links_to_points(client: Client, catalog: Catalog) -> None:
    _proposal(catalog, "Längere Öffnungszeiten", facility=catalog.bad)

    content = client.get("/vorschlaege/").content.decode()

    assert f'href="/verteilen/#ziel-f-{catalog.bad.pk}">Punkte geben' in content
