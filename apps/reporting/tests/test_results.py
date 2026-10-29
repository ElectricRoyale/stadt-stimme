import re

import pytest
from django.test import Client

from apps.access.models import Participant
from apps.catalog.models import Measure
from apps.points.services import Target, save_distribution
from apps.reporting.export import results_csv, safe_text
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
    assert results.gap_scale == 60


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

    payload = results_payload(build_results(build_overview()))

    assert [p["name"] for p in payload["places"]] == ["Hallenbad"]
    assert payload["places"][0]["gapText"] == "+35"
    assert payload["places"][0]["tone"] == "citizens"
    assert payload["scale"] == 60


def _visible_detail(content: str) -> str:
    """Name der einen sichtbaren Detailansicht; alle anderen tragen ``hidden``."""
    pattern = r'data-detail="[^"]+">\s*<div class="panel__head"><div>\s*<h2[^>]*>([^<]+)'
    shown: list[str] = re.findall(pattern, content)
    assert len(shown) == 1, shown
    return shown[0]


def test_results_page_is_public(client: Client, scenario: Catalog) -> None:
    content = client.get(URL).content.decode()

    assert 'href="/ergebnisse/" aria-current="page"' in content
    assert "Bei „Hallenbad“ liegen Wunsch und Geld am weitesten auseinander" in content
    assert "Umgekehrt ist es bei „Grundschule“ (\u221255)." in content
    assert _visible_detail(content) == "Hallenbad"
    assert "Mit deinem Code mitmachen" in content
    assert "Von dir" not in content


def test_query_selects_detail_without_javascript(client: Client, scenario: Catalog) -> None:
    content = client.get(URL, {"ort": f"c-{scenario.bildung.pk}"}).content.decode()

    assert _visible_detail(content) == "Bildung"
    assert f'href="?ort=c-{scenario.bildung.pk}#auswahl"' in content
    assert "Dazu 0 Punkte für „Bildung allgemein“, ohne bestimmten Ort." in content


def test_detail_shows_amounts_and_measures(client: Client, scenario: Catalog) -> None:
    Measure.objects.create(facility=scenario.bad, title="Neue Duschen", status="beschlossen")

    content = client.get(URL, {"ort": f"f-{scenario.bad.pk}"}).content.decode()

    assert "60 von 100 Punkten" in content
    assert "100.000 € von 400.000 €" in content
    assert "Neue Duschen" in content


def test_own_points_shown_when_logged_in(
    logged_in: Client, participant: Participant, scenario: Catalog
) -> None:
    save_distribution(participant, {Target("f", scenario.bad.pk): 15})

    content = logged_in.get(URL).content.decode()

    assert "Von dir: <strong>15 Punkte</strong>" in content
    assert f'href="/verteilen/#ziel-f-{scenario.bad.pk}">Punkte geben</a>' in content


def test_empty_catalog_has_clear_message(client: Client) -> None:
    content = client.get(URL).content.decode()

    assert "Noch keine Einrichtungen" in content
    assert "Es sind noch keine Punkte vergeben" in content


def test_csv_lists_places_and_themes(client: Client, scenario: Catalog) -> None:
    response = client.get("/ergebnisse/tabelle.csv")
    text = response.content.decode("utf-8")

    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert 'filename="stadtstimme-ergebnisse.csv"' in response["Content-Disposition"]
    assert text.startswith("\ufeff# StadtStimme")
    lines = text.splitlines()
    assert lines[1].startswith("Art;Name;Thema;Adresse")
    assert "Einrichtung;Hallenbad;Sport;;60;25;35;60;100000,00" in lines
    assert "Ganzes Thema;Sport;Sport;;80;25;55;80;100000,00" in lines


def test_csv_guards_against_formulas(scenario: Catalog) -> None:
    scenario.bad.name = "=HYPERLINK()"
    scenario.bad.save()

    text = results_csv(build_results(build_overview()), "Mannheim")

    assert "'=HYPERLINK()" in text
    assert safe_text("-1") == "'-1"
    assert safe_text("Bad") == "Bad"
