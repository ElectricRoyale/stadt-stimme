from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.points.services import Target, save_distribution
from apps.reporting.map_data import map_payload
from apps.reporting.results import build_results
from apps.reporting.statistics import build_overview, share
from apps.reporting.tests.conftest import Catalog
from apps.reporting.tests.helpers import LAST_YEAR, new_person, spend

pytestmark = pytest.mark.django_db


def test_share_rounds_and_handles_zero() -> None:
    assert share(1, 3) == 33
    assert share(5, 0) == 0


def test_overview_compares_citizens_with_spending(catalog: Catalog) -> None:
    save_distribution(
        new_person(), {Target("f", catalog.bad.pk): 60, Target("c", catalog.sport.pk): 20}
    )
    save_distribution(new_person(), {Target("f", catalog.schule.pk): 20})
    spend(catalog.bad, "100000")
    spend(catalog.schule, "300000")
    spend(catalog.schule, "999999", year=LAST_YEAR - 1)  # älteres Jahr zählt nicht

    stats = build_overview()

    by_category = {t.category: t for t in stats.themes}
    sport, bildung = by_category[catalog.sport], by_category[catalog.bildung]
    assert (sport.places_share, sport.general_share, sport.spend_share) == (60, 20, 25)
    assert (bildung.citizen_share, bildung.spend_share) == (20, 75)
    assert stats.fiscal_year == LAST_YEAR
    assert stats.participants == 2
    assert stats.top_theme == sport
    assert stats.biggest_gap == sport
    assert stats.places[0].name == "Hallenbad"


def test_expired_points_are_not_counted(catalog: Catalog) -> None:
    person = new_person()
    save_distribution(person, {Target("f", catalog.bad.pk): 50})
    person.last_active_at = timezone.now() - timedelta(days=400)
    person.save(update_fields=["last_active_at"])

    stats = build_overview()

    assert stats.total_points == 0
    assert stats.participants == 0
    assert stats.top_theme is None


def test_own_points_per_theme(catalog: Catalog) -> None:
    mine = {Target("f", catalog.bad.pk): 10, Target("c", catalog.sport.pk): 5}

    stats = build_overview(mine)

    sport = next(t for t in stats.themes if t.category == catalog.sport)
    assert sport.mine == 15
    assert stats.mine_used == 15


def test_map_payload_lists_all_facilities_with_spend(catalog: Catalog) -> None:
    catalog.bad.latitude, catalog.bad.longitude = Decimal("50.1"), Decimal("9.1")
    catalog.bad.save()
    spend(catalog.bad, "100000")
    stats = build_overview()

    places = {p["name"]: p for p in map_payload(stats, build_results(stats))["places"]}

    assert places["Hallenbad"]["lat"] == pytest.approx(50.1)
    assert places["Hallenbad"]["spend"] == 100
    assert places["Grundschule"]["lat"] is None
    assert "themes" not in map_payload(stats, build_results(stats))


def test_average_points_per_participant(catalog: Catalog) -> None:
    save_distribution(new_person(), {Target("f", catalog.bad.pk): 60})
    save_distribution(new_person(), {Target("f", catalog.schule.pk): 21})

    assert build_overview().average_points == 40
