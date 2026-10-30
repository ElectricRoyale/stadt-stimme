from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth.models import Permission, User
from django.test import Client, override_settings
from django.utils import timezone
from pytest_django.fixtures import Settings

from apps.catalog.models import Facility, Measure
from apps.points.tests.conftest import Catalog, catalog
from apps.proposals.models import Proposal, ProposalStatus, Support
from apps.reporting.tests.helpers import new_person

__all__ = ["catalog"]

pytestmark = pytest.mark.django_db
URL = "/verwaltung/"
LONG_ANSWER = "Kommt im Frühjahr, die Mittel sind im Haushalt."


@pytest.fixture(autouse=True)
def demo(settings: Settings) -> None:
    settings.DEMO_MODE = True
    settings.ROOT_URLCONF = "apps.access.tests.urls_with_admin"


@pytest.fixture
def staff_client(client: Client) -> Client:
    client.force_login(User.objects.create_user("markus", is_staff=True, is_superuser=True))
    return client


def _proposal(catalog: Catalog, title: str, supports: int = 0, **fields: object) -> Proposal:
    proposal = Proposal.objects.create(
        participant=new_person(), title=title, category=catalog.sport, **fields
    )
    for _ in range(supports):
        Support.objects.create(proposal=proposal, participant=new_person())
    return proposal


def test_only_staff_gets_in(client: Client) -> None:
    assert client.get(URL)["Location"] == "/zugang/stadt/"
    client.force_login(User.objects.create_user("buerger"))
    assert client.get(URL)["Location"] == "/zugang/stadt/"


@override_settings(PROPOSAL_SUPPORT_THRESHOLD=2, PROPOSAL_REVIEW_DAYS=14)
def test_overview_lists_tasks_tabs_and_sums(staff_client: Client, catalog: Catalog) -> None:
    review = _proposal(catalog, "Rampe am Eingang", supports=2)
    _proposal(catalog, "Mehr Bänke im Park", supports=1)

    content = staff_client.get(URL).content.decode()

    assert "Wartet auf Sie" in content
    assert f'href="/verwaltung/vorschlaege/{review.pk}/"' in content
    assert "Noch 14 Tage" in content
    assert 'In Prüfung<span class="va-tabs__count">1</span>' in content
    assert "Mehr Bänke im Park" not in content  # anderer Tab
    assert "Mehr Bänke im Park" in staff_client.get(URL, {"tab": "sammelt"}).content.decode()
    assert "Hallenbad" in content and "Einrichtungen und Haushalt" in content
    assert "codes eingelöst" in content.lower()
    assert "Freigabe" not in content


def test_accept_with_answer_and_measure(staff_client: Client, catalog: Catalog) -> None:
    proposal = _proposal(catalog, "Längere Öffnungszeiten", facility=catalog.bad)
    measure = Measure.objects.create(external_id="M-1", facility=catalog.bad, title="Abendbad")
    url = f"{URL}vorschlaege/{proposal.pk}/"

    response = staff_client.post(
        url, {"verdict": "annehmen", "answer": LONG_ANSWER, "measure": measure.pk}
    )

    assert response.status_code == 302
    proposal.refresh_from_db()
    assert proposal.status == ProposalStatus.ACCEPTED
    assert (proposal.answer, proposal.measure, proposal.decided_at is not None) == (
        LONG_ANSWER,
        measure,
        True,
    )
    assert "Antwort der Stadt" in staff_client.get(url).content.decode()


def test_reject_needs_reason_and_drops_measure(staff_client: Client, catalog: Catalog) -> None:
    proposal = _proposal(catalog, "Doppelter Vorschlag")
    url = f"{URL}vorschlaege/{proposal.pk}/"

    short = staff_client.post(url, {"verdict": "ablehnen", "answer": "Nein."})
    assert short.status_code == 422
    assert "mindestens 20 Zeichen" in short.content.decode()

    measure = Measure.objects.create(external_id="M-2", facility=catalog.bad, title="Egal")
    staff_client.post(url, {"verdict": "ablehnen", "answer": LONG_ANSWER, "measure": measure.pk})
    proposal.refresh_from_db()
    assert proposal.status == ProposalStatus.REJECTED and proposal.measure is None


def test_accepted_new_place_becomes_facility(staff_client: Client, catalog: Catalog) -> None:
    proposal = _proposal(
        catalog, "Bolzplatz am Neckar", latitude=Decimal("49.48"), longitude=Decimal("8.47")
    )

    staff_client.post(
        f"{URL}vorschlaege/{proposal.pk}/", {"verdict": "annehmen", "answer": LONG_ANSWER}
    )

    assert (
        Facility.objects.get(external_id=f"VORSCHLAG-{proposal.pk}").name == "Bolzplatz am Neckar"
    )


def test_decided_proposal_cannot_be_decided_again(staff_client: Client, catalog: Catalog) -> None:
    proposal = _proposal(catalog, "Schon entschieden", status=ProposalStatus.REJECTED)

    response = staff_client.post(
        f"{URL}vorschlaege/{proposal.pk}/", {"verdict": "annehmen", "answer": LONG_ANSWER}
    )

    proposal.refresh_from_db()
    assert response.status_code == 200 and proposal.status == ProposalStatus.REJECTED


def test_deciding_needs_change_permission(client: Client, catalog: Catalog) -> None:
    viewer = User.objects.create_user("lesend", is_staff=True)
    viewer.user_permissions.add(Permission.objects.get(codename="view_proposal"))
    client.force_login(viewer)
    proposal = _proposal(catalog, "Nur ansehen")

    url = f"{URL}vorschlaege/{proposal.pk}/"
    assert client.get(url).status_code == 200
    assert client.post(url, {"verdict": "annehmen", "answer": LONG_ANSWER}).status_code == 403


def test_snapshot_csv_from_the_log(staff_client: Client, catalog: Catalog) -> None:
    from apps.points.services import Target, save_distribution

    save_distribution(new_person(), {Target("f", catalog.bad.pk): 30})
    save_distribution(
        new_person(), {Target("f", catalog.bad.pk): 20, Target("c", catalog.sport.pk): 5}
    )

    assert "CSV herunterladen" in staff_client.get(URL).content.decode()
    response = staff_client.get(f"{URL}stichtag.csv", {"datum": timezone.localdate().isoformat()})

    assert response.status_code == 200
    lines = response.content.decode("utf-8-sig").splitlines()
    assert lines[1:] == [
        "Art;Name;Thema;Punkte;Unterstützer",
        "Einrichtung;Hallenbad;Sport;50;2",
        "Ganzes Thema;Sport allgemein;Sport;5;1",
    ]
    yesterday = timezone.localdate() - timedelta(days=1)
    empty = staff_client.get(f"{URL}stichtag.csv", {"datum": yesterday.isoformat()})
    assert empty.content.decode("utf-8-sig").splitlines()[1:] == [
        "Art;Name;Thema;Punkte;Unterstützer"
    ]


def test_snapshot_needs_a_valid_date(staff_client: Client) -> None:
    assert staff_client.get(f"{URL}stichtag.csv", {"datum": "gestern"}).status_code == 400
    assert staff_client.get(f"{URL}stichtag.csv").status_code == 400


def test_mark_facility_done_returns_points(staff_client: Client, catalog: Catalog) -> None:
    from apps.points.models import PointEvent, PointEventKind
    from apps.points.services import Target, points_of, save_distribution

    anna, ben = new_person(), new_person()
    save_distribution(anna, {Target("f", catalog.bad.pk): 30, Target("c", catalog.sport.pk): 5})
    save_distribution(ben, {Target("f", catalog.bad.pk): 20})
    url = f"{URL}einrichtungen/{catalog.bad.pk}/erledigt/"

    assert "Als erledigt markieren" in staff_client.get(URL).content.decode()
    confirm = staff_client.get(url).content.decode()
    assert "Hallenbad als erledigt markieren?" in confirm
    assert "<dd>50</dd>" in confirm and "<dd>2</dd>" in confirm

    response = staff_client.post(url, follow=True)

    assert "50 Punkte sind an 2 Personen zurückgegangen" in response.content.decode()
    assert points_of(anna) == {Target("c", catalog.sport.pk): 5}
    assert points_of(ben) == {}
    catalog.bad.refresh_from_db()
    assert catalog.bad.done_at is not None
    returned = PointEvent.objects.filter(kind=PointEventKind.RETURNED)
    assert sorted(returned.values_list("delta", flat=True)) == [-30, -20]
    assert not returned.filter(measure__isnull=False).exists()


def test_marking_done_needs_change_permission(client: Client, catalog: Catalog) -> None:
    from apps.points.services import Target, points_of, save_distribution

    person = new_person()
    save_distribution(person, {Target("f", catalog.bad.pk): 30})
    client.force_login(User.objects.create_user("lesend", is_staff=True))
    url = f"{URL}einrichtungen/{catalog.bad.pk}/erledigt/"

    assert "Recht „Einrichtung ändern“" in client.get(url).content.decode()
    assert client.post(url).status_code == 403
    assert points_of(person) == {Target("f", catalog.bad.pk): 30}
