import pytest
from django.test import Client

from apps.access.models import Participant
from apps.points.services import Target, save_distribution
from apps.reporting.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db
URL = "/uebersicht/"


def test_overview_is_public(client: Client, catalog: Catalog) -> None:
    response = client.get(URL)

    content = response.content.decode()
    assert response.status_code == 200
    assert "<h1>Übersicht</h1>" in content
    assert "Wunsch und Haushalt" in content
    assert "Neu in Musterstadt" in content
    assert 'href="/zugang/">Code eingeben' in content
    assert 'data-scope="meine"' not in content
    assert 'id="ov-map-data"' in content


def test_overview_shows_own_points_when_logged_in(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(
        participant, {Target("f", catalog.bad.pk): 30, Target("c", catalog.sport.pk): 5}
    )

    content = logged_in.get(URL).content.decode()

    assert '<span class="btn-ink__tag">65 frei</span>' in content
    assert "35 vergeben, 65 frei" in content
    color = catalog.sport.color
    assert content.count(f'class="mp__cell is-given theme-{color}"') == 30
    assert content.count(f'class="mp__cell is-given theme-{color} is-general"') == 5
    assert "Hallenbad, Sport allgemein" in content
    assert 'data-scope="meine"' in content
    assert "Neu bei deinen Einrichtungen" in content


def test_navigation_shows_free_points(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 80})

    content = logged_in.get("/ergebnisse/").content.decode()

    assert "20 frei" in content
    assert "20 Punkte frei" in content


def test_lead_theme_is_marked(client: Client, catalog: Catalog) -> None:
    save_distribution(new_person(), {Target("f", catalog.schule.pk): 40})

    content = client.get(URL).content.decode()

    assert "Bildung bekommt 100 % der Bürgerpunkte" in content
    assert content.count("wb-line--lead") == 1


def test_map_data_is_escaped(client: Client, catalog: Catalog) -> None:
    catalog.bad.name = "</script><script>alert(1)</script>"
    catalog.bad.latitude, catalog.bad.longitude = 50, 9
    catalog.bad.save()

    content = client.get(URL).content.decode()

    assert "<script>alert(1)</script>" not in content


def test_login_page_links_to_overview(client: Client) -> None:
    assert 'href="/uebersicht/"' in client.get("/zugang/").content.decode()
