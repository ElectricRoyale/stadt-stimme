"""Stichtagswerte aus dem Log (M7): reproduzierbar, unabhängig vom heutigen Stand."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.points.models import PointEvent
from apps.points.services import Target, save_distribution
from apps.points.snapshot import tally_at
from apps.points.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


def test_tally_counts_points_and_supporters_at_a_moment(catalog: Catalog) -> None:
    anna, ben = new_person(), new_person()
    bad, sport = Target("f", catalog.bad.pk), Target("c", catalog.sport.pk)
    save_distribution(anna, {bad: 30, sport: 10})
    save_distribution(ben, {bad: 20})
    moment = timezone.now()

    save_distribution(anna, {sport: 50})  # danach umverteilt

    then = tally_at(moment)
    assert {t: (v.points, v.supporters) for t, v in then.items()} == {
        bad: (50, 2),
        sport: (10, 1),
    }
    now = tally_at(timezone.now())
    assert {t: (v.points, v.supporters) for t, v in now.items()} == {
        bad: (20, 1),
        sport: (50, 1),
    }


def test_tally_before_any_event_is_empty(catalog: Catalog) -> None:
    save_distribution(new_person(), {Target("f", catalog.bad.pk): 30})
    first = PointEvent.objects.get().created_at

    assert tally_at(first - timedelta(seconds=1)) == {}
