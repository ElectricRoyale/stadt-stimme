import pytest
from django.test import Client

from apps.access.models import Participant
from apps.points.services import Target, points_of, save_distribution
from apps.points.tests.conftest import Catalog

pytestmark = pytest.mark.django_db
URL = "/verteilen/"


def test_requires_login(client: Client) -> None:
    response = client.get(URL)

    assert response.status_code == 302
    assert response["Location"] == "/zugang/"


def test_shows_themes_with_general_row_and_facilities(logged_in: Client, catalog: Catalog) -> None:
    content = logged_in.get(URL).content.decode()

    assert "Sport allgemein" in content
    assert "Hallenbad" in content
    assert "Grundschule" in content
    assert f'name="c-{catalog.sport.pk}"' in content
    assert f'name="f-{catalog.bad.pk}"' in content
    assert 'aria-label="Punkte für Hallenbad"' in content
    assert "100</span>" in content  # alle Punkte frei


def test_shows_current_points(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 35})

    content = logged_in.get(URL).content.decode()

    assert 'value="35"' in content
    assert '<span class="budget__number" data-remaining>65</span>' in content


def test_post_saves_and_redirects(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    response = logged_in.post(URL, {f"f-{catalog.bad.pk}": "40", f"c-{catalog.sport.pk}": "10"})

    assert response.status_code == 302
    assert points_of(participant) == {
        Target("f", catalog.bad.pk): 40,
        Target("c", catalog.sport.pk): 10,
    }
    assert "Deine Verteilung ist gespeichert." in logged_in.get(URL).content.decode()


def test_post_over_budget_shows_error_and_keeps_old_state(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 5})

    response = logged_in.post(URL, {f"f-{catalog.bad.pk}": "70", f"f-{catalog.schule.pk}": "40"})

    content = response.content.decode()
    assert response.status_code == 422
    assert 'role="alert"' in content
    assert "110 Punkte verteilt" in content
    assert points_of(participant) == {Target("f", catalog.bad.pk): 5}


def test_post_rejects_negative_numbers(logged_in: Client, catalog: Catalog) -> None:
    response = logged_in.post(URL, {f"f-{catalog.bad.pk}": "-3"})

    assert response.status_code == 422
    assert 'aria-invalid="true"' in response.content.decode()


def test_unknown_targets_are_ignored(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    response = logged_in.post(URL, {"f-999999": "50", f"f-{catalog.bad.pk}": "5"})

    assert response.status_code == 302
    assert points_of(participant) == {Target("f", catalog.bad.pk): 5}
