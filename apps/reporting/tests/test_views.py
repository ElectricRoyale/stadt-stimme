import pytest
from django.test import Client

from apps.access.models import Participant
from apps.points.services import Target, save_distribution
from apps.reporting.tests.conftest import Catalog

pytestmark = pytest.mark.django_db
URL = "/uebersicht/"


def test_overview_is_public(client: Client, catalog: Catalog) -> None:
    response = client.get(URL)

    content = response.content.decode()
    assert response.status_code == 200
    assert "Musterstadt auf einen Blick" in content
    assert "Code eingeben" in content
    assert "Nur meine Punkte" not in content
    assert 'id="dash-map-data"' in content


def test_overview_shows_own_points_when_logged_in(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    content = logged_in.get(URL).content.decode()

    assert "<strong>70</strong> von 100 Punkten noch frei" in content
    assert "Nur meine Punkte" in content
    assert "Du hast <strong>30 vergeben</strong>" in content


def test_map_data_is_escaped(client: Client, catalog: Catalog) -> None:
    catalog.bad.name = "</script><script>alert(1)</script>"
    catalog.bad.latitude, catalog.bad.longitude = 50, 9
    catalog.bad.save()

    content = client.get(URL).content.decode()

    assert "<script>alert(1)</script>" not in content


def test_login_page_links_to_overview(client: Client) -> None:
    assert 'href="/uebersicht/"' in client.get("/zugang/").content.decode()
