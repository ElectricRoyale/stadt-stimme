import re

import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission, User
from django.test import Client, RequestFactory
from django.utils import timezone

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
        "facility": catalog.bad.pk,
    }
    data.update(changes)
    return data


def test_page_is_public_but_submitting_needs_code(client: Client, catalog: Catalog) -> None:
    content = client.get(URL).content.decode()

    assert "Der Weg eines Vorschlags" in content
    assert "Zum Einreichen brauchst du den Code" in content
    assert client.post(URL, _data(catalog))["Location"] == "/zugang/"
    assert not Proposal.objects.exists()


def test_submit_shows_sent_state(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    response = logged_in.post(URL, _data(catalog))

    proposal = Proposal.objects.get()
    assert response["Location"] == f"/vorschlaege/?eingereicht={proposal.pk}#vorschlag-neu"
    assert (proposal.participant, proposal.facility) == (participant, catalog.bad)
    page = logged_in.get(response["Location"]).content.decode()
    assert f"Vorschlag V-{proposal.pk} eingereicht" in page
    assert "ab sofort öffentlich" in page
    assert "Dein Vorschlag" in page


def test_sent_state_only_for_own_proposal(logged_in: Client, catalog: Catalog) -> None:
    foreign = Proposal.objects.create(
        participant=new_person(), title="Fremder Vorschlag", category=catalog.sport
    )

    page = logged_in.get(URL, {"eingereicht": foreign.pk}).content.decode()

    assert "eingereicht</h3>" not in page
    assert "Fremder Vorschlag" in page  # sofort öffentlich, aber ohne Bestätigung


def test_general_proposal_without_facility(logged_in: Client, catalog: Catalog) -> None:
    logged_in.post(URL, _data(catalog, facility=""))

    assert Proposal.objects.get().facility is None


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"title": "Zu kurz"}, "mindestens 8 Zeichen"),
        ({"category": ""}, "Wähle ein Thema"),
        ({"category": "BILDUNG"}, "gehört nicht zum Thema"),
    ],
)
def test_invalid_input_is_reported(
    logged_in: Client, catalog: Catalog, changes: dict[str, object], message: str
) -> None:
    if changes.get("category") == "BILDUNG":
        changes = {"category": catalog.bildung.pk}
    response = logged_in.post(URL, _data(catalog, **changes))

    assert response.status_code == 422
    assert message in response.content.decode()
    assert not Proposal.objects.exists()


def test_list_shows_stages_and_answer(client: Client, catalog: Catalog) -> None:
    now = timezone.now()
    Proposal.objects.create(
        participant=new_person(), title="Gerade eingereicht", category=catalog.sport
    )
    Proposal.objects.create(
        participant=new_person(),
        title="Längere Öffnungszeiten",
        category=catalog.sport,
        status=ProposalStatus.ACCEPTED,
        decided_at=now,
        answer="Kommt ab Januar.",
    )

    content = client.get(URL).content.decode()

    assert "Gerade eingereicht" in content
    assert "Längere Öffnungszeiten" in content
    assert "Kommt ab Januar." in content
    assert 'data-stage="angenommen"' in content
    assert "Freigabe" not in content


def test_stage_filter_without_javascript(client: Client, catalog: Catalog) -> None:
    Proposal.objects.create(
        participant=new_person(),
        title="Sammelt noch Stimmen",
        category=catalog.sport,
    )

    content = client.get(URL, {"schritt": "angenommen"}).content.decode()

    assert "Nur Schritt <strong data-stage-name>Angenommen</strong>" in content
    assert re.search(r'data-stage="sammelt"[^>]*hidden>', content)


def test_similar_and_support(logged_in: Client, catalog: Catalog) -> None:
    proposal = Proposal.objects.create(
        participant=new_person(),
        title="Abendöffnung im Hallenbad",
        category=catalog.sport,
        status=ProposalStatus.OPEN,
    )

    items = logged_in.get("/vorschlaege/aehnlich/", {"q": "Hallenbad abends"}).json()["items"]
    response = logged_in.post(f"/vorschlaege/{proposal.pk}/unterstuetzen/")

    assert [i["title"] for i in items] == ["Abendöffnung im Hallenbad"]
    assert items[0]["canSupport"] is True
    data = response.json()
    assert (data["supported"], data["supports"], data["stage"]) == (True, 1, "sammelt")
    assert data["sentence"] == "1 von 50 Unterstützungen, noch 49 bis zur Prüfung."


def test_support_needs_code_and_open_proposal(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    decided = Proposal.objects.create(
        participant=new_person(),
        title="Schon entschieden",
        category=catalog.sport,
        status=ProposalStatus.REJECTED,
    )
    fresh = Proposal.objects.create(
        participant=new_person(), title="Gerade eingereicht", category=catalog.sport
    )
    own = Proposal.objects.create(
        participant=participant,
        title="Mein eigener",
        category=catalog.sport,
        status=ProposalStatus.OPEN,
    )

    assert logged_in.post(f"/vorschlaege/{decided.pk}/unterstuetzen/").status_code == 404
    assert logged_in.post(f"/vorschlaege/{fresh.pk}/unterstuetzen/").status_code == 200
    assert logged_in.post(f"/vorschlaege/{own.pk}/unterstuetzen/").status_code == 400
    assert Client().post(f"/vorschlaege/{own.pk}/unterstuetzen/").status_code == 403


def test_decisions_need_change_permission() -> None:
    viewer = User.objects.create_user("lesend", is_staff=True)
    viewer.user_permissions.add(Permission.objects.get(codename="view_proposal"))
    request = RequestFactory().get("/admin/proposals/proposal/")
    request.user = viewer
    model_admin = admin.site._registry[Proposal]

    actions = model_admin.get_actions(request)
    assert "accept" not in actions and "reject" not in actions
    assert "publish" not in actions
