import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.test import Client, RequestFactory

from apps.access.models import Participant
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db
URL = "/vorschlaege/"


def _data(catalog: Catalog, **changes: object) -> dict[str, object]:
    data: dict[str, object] = {
        "title": "Abendöffnung im Hallenbad",
        "text": "Nach der Arbeit ist es zu.",
        "category": catalog.sport.pk,
        "where": "place",
        "facility": catalog.bad.pk,
    }
    data.update(changes)
    return data


def test_page_is_public_but_submitting_needs_code(client: Client, catalog: Catalog) -> None:
    content = client.get(URL).content.decode()

    assert "Was soll die Stadt angehen?" in content
    assert "Zum Einreichen brauchst du den Code" in content
    assert client.post(URL, _data(catalog))["Location"] == "/zugang/"
    assert not Proposal.objects.exists()


def test_submit_redirects_to_thanks(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    response = logged_in.post(URL, _data(catalog))

    proposal = Proposal.objects.get()
    assert response["Location"] == f"/vorschlaege/{proposal.pk}/danke/"
    assert (proposal.participant, proposal.facility) == (participant, catalog.bad)
    thanks = logged_in.get(response["Location"]).content.decode()
    assert f"Nummer V-{proposal.pk}" in thanks
    assert "innerhalb von 14 Tagen" in thanks


def test_general_proposal_drops_facility(logged_in: Client, catalog: Catalog) -> None:
    logged_in.post(URL, _data(catalog, where="none"))

    assert Proposal.objects.get().facility is None


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"title": "Zu kurz"}, "mindestens 8 Zeichen"),
        ({"category": ""}, "Bitte wähle ein Thema."),
        ({"facility": ""}, "Bitte wähle einen Ort"),
    ],
)
def test_invalid_input_is_reported(
    logged_in: Client, catalog: Catalog, changes: dict[str, object], message: str
) -> None:
    response = logged_in.post(URL, _data(catalog, **changes))

    assert response.status_code == 422
    assert message in response.content.decode()
    assert not Proposal.objects.exists()


def test_thanks_only_for_own_proposal(logged_in: Client, catalog: Catalog) -> None:
    foreign = Proposal.objects.create(
        participant=new_person(), title="Fremder Vorschlag", category=catalog.sport
    )

    assert logged_in.get(f"/vorschlaege/{foreign.pk}/danke/").status_code == 404


def test_similar_and_support(logged_in: Client, catalog: Catalog) -> None:
    proposal = Proposal.objects.create(
        participant=new_person(),
        title="Abendöffnung im Hallenbad",
        category=catalog.sport,
        status=ProposalStatus.PUBLISHED,
    )

    items = logged_in.get("/vorschlaege/aehnlich/", {"q": "Hallenbad abends"}).json()["items"]
    response = logged_in.post(f"/vorschlaege/{proposal.pk}/unterstuetzen/")

    assert [i["title"] for i in items] == ["Abendöffnung im Hallenbad"]
    assert response.json() == {"supported": True, "supports": 1}


def test_support_needs_code_and_published_proposal(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    hidden = Proposal.objects.create(
        participant=new_person(), title="Noch nicht frei", category=catalog.sport
    )
    own = Proposal.objects.create(
        participant=participant,
        title="Mein eigener",
        category=catalog.sport,
        status=ProposalStatus.PUBLISHED,
    )

    assert logged_in.post(f"/vorschlaege/{hidden.pk}/unterstuetzen/").status_code == 404
    assert logged_in.post(f"/vorschlaege/{own.pk}/unterstuetzen/").status_code == 400
    assert Client().post(f"/vorschlaege/{own.pk}/unterstuetzen/").status_code == 403


def test_publish_needs_change_permission() -> None:
    viewer = User.objects.create_user("lesend", is_staff=True)
    viewer.user_permissions.add(Permission.objects.get(codename="view_proposal"))
    request = RequestFactory().get("/admin/proposals/proposal/")
    request.user = viewer
    model_admin = admin.site._registry[Proposal]

    assert "publish" not in model_admin.get_actions(request)
