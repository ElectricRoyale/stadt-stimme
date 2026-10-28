import pytest
from django.test import Client

from apps.access.models import Participant
from apps.points.services import Target, save_distribution
from apps.reporting.map_data import results_payload
from apps.reporting.results import build_results
from apps.reporting.statistics import build_overview
from apps.reporting.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person, spend

pytestmark = pytest.mark.django_db
URL = "/ergebnisse/"


@pytest.fixture
def scenario(catalog: Catalog) -> Catalog:
    """Hallenbad 60 % Wunsch / 25 % Geld, Grundschule 20 % / 75 %, Sport allgemein 20 %."""
    save_distribution(
        new_person(), {Target("f", catalog.bad.pk): 60, Target("c", catalog.sport.pk): 20}
    )
    save_distribution(new_person(), {Target("f", catalog.schule.pk): 20})
    spend(catalog.bad, "100000")
    spend(catalog.schule, "300000")
    return catalog


def test_gap_per_place_and_theme(scenario: Catalog) -> None:
    results = build_results(build_overview())

    places = {r.name: (r.wish, r.spend, r.gap_text, r.tone) for r in results.places}
    themes = {r.name: (r.wish, r.spend, r.gap_text) for r in results.themes}
    assert places == {
        "Hallenbad": (60, 25, "+35", "citizens"),
        "Sporthalle": (0, 0, "\u00b10", "even"),
        "Grundschule": (20, 75, "\u221255", "city"),
    }
    assert themes == {"Sport": (80, 25, "+55"), "Bildung": (20, 75, "\u221255")}
    assert [r.name for r in results.places] == ["Hallenbad", "Sporthalle", "Grundschule"]
    assert results.scale_max == 80


def test_select_falls_back_to_biggest_gap(scenario: Catalog) -> None:
    results = build_results(build_overview())

    def name(key: str | None) -> str | None:
        row = results.select(key)
        return row.name if row else None

    assert name(f"f-{scenario.schule.pk}") == "Grundschule"
    assert name("f-999") == "Hallenbad"
    assert name(None) == "Hallenbad"


def test_payload_marks_only_located_places(scenario: Catalog) -> None:
    scenario.bad.latitude, scenario.bad.longitude = 50.1, 9.1
    scenario.bad.save()

    rows = results_payload(build_results(build_overview()), "/verteilen/")["rows"]

    located = [r["name"] for r in rows if r["lat"] is not None]
    assert located == ["Hallenbad"]
    assert rows[0]["give"] == f"/verteilen/#id_f-{scenario.bad.pk}"


def test_results_page_is_public(client: Client, scenario: Catalog) -> None:
    content = client.get(URL).content.decode()

    assert "Wo passen Wunsch und Geld zusammen?" in content
    assert 'aria-current="page">Ergebnisse' in content
    assert '<h2 id="res-detail-title" data-field="name">Hallenbad</h2>' in content
    assert "Von dir" not in content


def test_query_selects_detail_without_javascript(client: Client, scenario: Catalog) -> None:
    content = client.get(URL, {"ort": f"c-{scenario.bildung.pk}"}).content.decode()

    assert '<h2 id="res-detail-title" data-field="name">Bildung</h2>' in content
    assert "Punkte an „Bildung allgemein“ geben" in content


def test_own_points_shown_when_logged_in(
    logged_in: Client, participant: Participant, scenario: Catalog
) -> None:
    save_distribution(participant, {Target("f", scenario.bad.pk): 15})

    content = logged_in.get(URL).content.decode()

    assert '<strong data-field="mine">15 Punkte</strong>' in content


def test_empty_catalog_has_clear_message(client: Client) -> None:
    content = client.get(URL).content.decode()

    assert "Noch keine Einrichtungen" in content
    assert "Es sind noch keine Punkte vergeben" in content
