from datetime import date, datetime, timedelta

import pytest
from django.utils import timezone

from apps.access.models import AccessCode
from apps.catalog.models import Measure
from apps.points.services import Target, save_distribution
from apps.reporting.dashboard import (
    NewsItem,
    my_points,
    nice_top,
    participation_by_week,
    recent_measures,
    wish_budget,
)
from apps.reporting.results import build_results
from apps.reporting.statistics import build_overview
from apps.reporting.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person, spend

pytestmark = pytest.mark.django_db


def test_wish_budget_sorts_by_gap_and_marks_lead(catalog: Catalog) -> None:
    save_distribution(new_person(), {Target("f", catalog.bad.pk): 60})
    save_distribution(new_person(), {Target("f", catalog.schule.pk): 40})
    spend(catalog.schule, "900000")
    spend(catalog.bad, "100000")
    stats = build_overview()

    wish = wish_budget(stats, build_results(stats))

    assert [line.theme.category for line in wish.lines] == [catalog.sport, catalog.bildung]
    sport, bildung = wish.lines
    assert sport.is_lead and not bildung.is_lead
    assert (sport.gap_text, bildung.gap_text) == ("+50", "\N{MINUS SIGN}50")
    assert wish.axis_max == 100
    assert wish.ticks == [0, 20, 40, 60, 80, 100]
    assert [r.name for r in sport.places] == ["Hallenbad", "Sporthalle"]
    assert sport.general is not None and sport.general.name == "Sport allgemein"


def test_label_stays_inside_the_track(catalog: Catalog) -> None:
    save_distribution(new_person(), {Target("f", catalog.bad.pk): 90})
    save_distribution(new_person(), {Target("f", catalog.schule.pk): 10})
    spend(catalog.schule, "100")
    stats = build_overview()

    lines = {ln.theme.category: ln for ln in wish_budget(stats, build_results(stats)).lines}

    assert lines[catalog.sport].label_position == "inside"  # 90 % gegen 0 %
    assert lines[catalog.bildung].label_position == "between"  # 10 % gegen 100 %


def test_my_points_fill_hundred_cells(catalog: Catalog) -> None:
    mine = {Target("f", catalog.bad.pk): 30, Target("c", catalog.sport.pk): 10}

    points = my_points(build_overview(mine))

    assert len(points.cells) == 100
    assert sum(1 for c in points.cells if c.category_pk and not c.general) == 30
    assert sum(1 for c in points.cells if c.general) == 10
    assert points.cells[29].general is False and points.cells[30].general is True
    assert (points.used, points.free) == (40, 60)
    assert [(t.category, t.total, t.names) for t in points.themes] == [
        (catalog.sport, 40, ["Hallenbad", "Sport allgemein"])
    ]


def test_my_points_without_points_are_all_free(catalog: Catalog) -> None:
    points = my_points(build_overview())

    assert points.themes == []
    assert all(c.category_pk is None for c in points.cells)
    assert points.free == 100


def test_participation_counts_redeemed_codes_per_week(db: None) -> None:
    today = date(2026, 10, 29)  # Donnerstag, KW 44
    for days_ago in (0, 1, 7, 60):
        person = new_person()
        moment = timezone.make_aware(datetime(2026, 10, 29, 12)) - timedelta(days=days_ago)
        AccessCode.objects.filter(pk=person.access_code_id).update(redeemed_at=moment)

    participation = participation_by_week(weeks=3, today=today)

    assert [w.week for w in participation.weeks] == [42, 43, 44]
    assert [w.count for w in participation.weeks] == [0, 1, 2]
    assert participation.current.is_current
    assert participation.top == 4
    assert participation.height(participation.current) == 50.0


@pytest.mark.parametrize(("value", "top"), [(0, 4), (3, 4), (7, 7), (12, 20), (213, 300)])
def test_nice_top(value: int, top: int) -> None:
    assert nice_top(value) == top


def test_recent_measures_newest_first_and_filtered(catalog: Catalog) -> None:
    old = Measure.objects.create(external_id="M-1", facility=catalog.bad, title="Alt")
    new = Measure.objects.create(external_id="M-2", facility=catalog.schule, title="Neu")
    Measure.objects.filter(pk=old.pk).update(updated_at=timezone.now() - timedelta(days=3))

    assert [i.measure for i in recent_measures(None)] == [new, old]
    assert recent_measures({catalog.bad.pk: 25}) == [NewsItem(old, 25)]
    assert recent_measures({}) == []
