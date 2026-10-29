"""Ort eines Vorschlags: allgemein, bekannte Einrichtung oder Punkt auf der Karte (ADR-022)."""

from decimal import Decimal

import pytest
from django.contrib import admin
from django.db import IntegrityError
from django.test import Client, RequestFactory

from apps.access.models import Participant
from apps.proposals.admin import ProposalAdmin
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import place_from_proposal
from apps.proposals.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db
URL = "/vorschlaege/"


def _data(catalog: Catalog, **changes: object) -> dict[str, object]:
    data: dict[str, object] = {
        "title": "Zebrastreifen an der Kreuzung",
        "category": catalog.sport.pk,
        "where": "neu",
        "latitude": "49.487459",
        "longitude": "8.466039",
    }
    data.update(changes)
    return data


def test_new_place_saves_point_without_facility(logged_in: Client, catalog: Catalog) -> None:
    response = logged_in.post(URL, _data(catalog, facility=catalog.bad.pk))

    assert response.status_code == 302
    proposal = Proposal.objects.get()
    assert proposal.facility is None
    assert (proposal.latitude, proposal.longitude) == (Decimal("49.487459"), Decimal("8.466039"))
    assert proposal.where == "Neuer Ort auf der Karte"


def test_new_place_needs_a_point(logged_in: Client, catalog: Catalog) -> None:
    response = logged_in.post(URL, _data(catalog, latitude="", longitude=""))

    assert response.status_code == 422
    assert "Tippe auf die Karte" in response.content.decode()
    assert not Proposal.objects.exists()


def test_point_out_of_range_is_rejected(logged_in: Client, catalog: Catalog) -> None:
    response = logged_in.post(URL, _data(catalog, latitude="91"))

    assert response.status_code == 422
    assert not Proposal.objects.exists()


def test_known_place_needs_facility(logged_in: Client, catalog: Catalog) -> None:
    response = logged_in.post(URL, _data(catalog, where="bekannt"))

    assert response.status_code == 422
    assert "Wähle die Einrichtung" in response.content.decode()


def test_known_place_drops_point(logged_in: Client, catalog: Catalog) -> None:
    logged_in.post(URL, _data(catalog, where="bekannt", facility=catalog.bad.pk))

    proposal = Proposal.objects.get()
    assert proposal.facility == catalog.bad
    assert proposal.latitude is None


def test_general_drops_facility_and_point(logged_in: Client, catalog: Catalog) -> None:
    logged_in.post(URL, _data(catalog, where="allgemein"))

    proposal = Proposal.objects.get()
    assert (proposal.facility, proposal.latitude) == (None, None)
    assert proposal.where == "Kein bestimmter Ort"


def test_page_offers_three_choices(logged_in: Client, catalog: Catalog) -> None:
    content = logged_in.get(URL).content.decode()

    for label in ("Nein, allgemein", "Ja, bekannter Ort", "Ja, neuer Ort"):
        assert label in content
    assert "data-pick-map" in content
    assert 'id="v-karte-orte"' in content


def test_database_refuses_facility_and_point(participant: Participant, catalog: Catalog) -> None:
    with pytest.raises(IntegrityError):
        Proposal.objects.create(
            participant=participant,
            title="Beides zugleich",
            category=catalog.sport,
            facility=catalog.bad,
            latitude=Decimal("49.5"),
            longitude=Decimal("8.5"),
        )


def _new_place(catalog: Catalog) -> Proposal:
    return Proposal.objects.create(
        participant=new_person(),
        title="Zebrastreifen an der Kreuzung",
        category=catalog.sport,
        status=ProposalStatus.PUBLISHED,
        latitude=Decimal("49.487459"),
        longitude=Decimal("8.466039"),
    )


def test_accepting_new_place_creates_own_facility(catalog: Catalog) -> None:
    proposal = _new_place(catalog)
    request = RequestFactory().post("/admin/proposals/proposal/")
    model_admin = admin.site._registry[Proposal]
    assert isinstance(model_admin, ProposalAdmin)

    model_admin.accept(request, Proposal.objects.filter(pk=proposal.pk))

    proposal.refresh_from_db()
    facility = proposal.facility
    assert facility is not None
    assert (facility.name, facility.category, facility.external_id) == (
        "Zebrastreifen an der Kreuzung",
        catalog.sport,
        f"VORSCHLAG-{proposal.pk}",
    )
    assert (facility.latitude, facility.longitude) == (Decimal("49.487459"), Decimal("8.466039"))
    assert proposal.latitude is None
    assert place_from_proposal(proposal) is None  # nur einmal


def test_new_place_is_its_own_row_after_acceptance(logged_in: Client, catalog: Catalog) -> None:
    proposal = _new_place(catalog)
    proposal.status = ProposalStatus.ACCEPTED
    proposal.save()
    facility = place_from_proposal(proposal)
    assert facility is not None

    content = logged_in.get("/verteilen/").content.decode()

    assert f'name="f-{facility.pk}"' in content
    assert f"Angenommener Vorschlag V-{proposal.pk}:" in content


def test_known_and_general_places_create_no_facility(catalog: Catalog) -> None:
    known = Proposal.objects.create(
        participant=new_person(),
        title="Abends länger",
        category=catalog.sport,
        facility=catalog.bad,
    )
    general = Proposal.objects.create(
        participant=new_person(), title="Mehr Kurse", category=catalog.sport
    )

    assert place_from_proposal(known) is None
    assert place_from_proposal(general) is None
