import pytest
from django.test import Client
from django.urls import reverse

from apps.catalog.models import Category, Facility, Measure
from apps.catalog.search import search

pytestmark = pytest.mark.django_db


@pytest.fixture
def pool() -> Facility:
    sport = Category.objects.create(name="Sport")
    pool = Facility.objects.create(
        external_id="E-1", name="Herschelbad", address="U3 1", category=sport
    )
    Measure.objects.create(external_id="M-1", facility=pool, title="Sauna sanieren")
    Measure.objects.create(external_id="M-2", facility=pool, title="Dach dämmen")
    return pool


def test_finds_facility_by_name_without_measures(pool: Facility) -> None:
    hits = search("herschel")
    assert [h.facility for h in hits] == [pool]
    assert hits[0].measures == []
    assert hits[0].target_key == f"f-{pool.pk}"


def test_finds_facility_by_measure_and_lists_only_matching_ones(pool: Facility) -> None:
    hits = search("sauna")
    assert [h.facility for h in hits] == [pool]
    assert [m.title for m in hits[0].measures] == ["Sauna sanieren"]


def test_all_words_must_match(pool: Facility) -> None:
    assert search("herschelbad u3") != []
    assert search("herschelbad turnhalle") == []


def test_short_query_finds_nothing(pool: Facility) -> None:
    assert search("h") == []


def test_page_is_public_and_links_to_results(client: Client, pool: Facility) -> None:
    response = client.get(reverse("catalog:search"), {"q": "sauna"})
    assert response.status_code == 200
    html = response.content.decode()
    assert "Herschelbad" in html
    assert f"?ort=f-{pool.pk}#auswahl" in html
    assert "Punkte geben" not in html


def test_page_reports_no_hits(client: Client, pool: Facility) -> None:
    response = client.get(reverse("catalog:search"), {"q": "turnhalle"})
    assert "Nichts gefunden" in response.content.decode()


def test_category_icon_follows_color() -> None:
    assert Category.objects.create(name="Bildung").icon == "graduation-cap"
    assert Category(name="Neu", color="").icon == "map-pin"
