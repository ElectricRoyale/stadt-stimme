"""Rückfluss bei „in Umsetzung“ (ADR-027): Transaktion, Ereignisse, Signal."""

from collections.abc import Callable
from typing import Any
from unittest import mock

import pytest
from django.test import Client

from apps.access.models import Participant
from apps.catalog.models import Measure, MeasureStatus
from apps.points.models import Allocation, PointEvent, PointEventKind
from apps.points.returns import ReturnedPoints, recent_changes, return_points
from apps.points.services import Target, points_of, save_distribution
from apps.points.signals import points_returned
from apps.points.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


@pytest.fixture
def measure(catalog: Catalog) -> Measure:
    return Measure.objects.create(external_id="M-1", facility=catalog.bad, title="Dach sanieren")


def _start(measure: Measure, status: str = MeasureStatus.IN_PROGRESS) -> None:
    measure.status = status
    measure.save()


def test_in_progress_returns_facility_points_and_keeps_the_rest(
    participant: Participant, catalog: Catalog, measure: Measure
) -> None:
    other = new_person()
    bad, halle, sport = (
        Target("f", catalog.bad.pk),
        Target("f", catalog.halle.pk),
        Target("c", catalog.sport.pk),
    )
    save_distribution(participant, {bad: 30, halle: 10, sport: 20})
    save_distribution(other, {bad: 50})

    _start(measure)

    assert points_of(participant) == {halle: 10, sport: 20}
    assert points_of(other) == {}
    returned = PointEvent.objects.filter(kind=PointEventKind.RETURNED).order_by("participant_id")
    assert [(e.participant_id, e.delta, e.measure_id) for e in returned] == [
        (participant.pk, -30, measure.pk),
        (other.pk, -50, measure.pk),
    ]


def test_signal_fires_only_after_commit(
    participant: Participant,
    catalog: Catalog,
    measure: Measure,
    django_capture_on_commit_callbacks: Callable[..., Any],
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    received: list[list[ReturnedPoints]] = []

    def listener(sender: Any, returns: list[ReturnedPoints], **kwargs: Any) -> None:
        received.append(returns)

    points_returned.connect(listener)
    try:
        with django_capture_on_commit_callbacks(execute=False) as callbacks:
            _start(measure)
        assert received == []
        for callback in callbacks:
            callback()
    finally:
        points_returned.disconnect(listener)

    assert received == [[ReturnedPoints(participant.pk, 30)]]


@pytest.mark.parametrize("status", [MeasureStatus.DECIDED, MeasureStatus.REJECTED])
def test_other_statuses_keep_points(
    participant: Participant, catalog: Catalog, measure: Measure, status: str
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    _start(measure, status)

    assert points_of(participant) == {Target("f", catalog.bad.pk): 30}


def test_points_given_during_progress_stay(
    participant: Participant, catalog: Catalog, measure: Measure
) -> None:
    _start(measure)
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    _start(measure)  # erneut gespeichert, Status unverändert
    _start(measure, MeasureStatus.COMPLETED)

    assert points_of(participant) == {Target("f", catalog.bad.pk): 30}


def test_new_measure_already_in_progress_returns_points(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    Measure.objects.create(
        external_id="M-2", facility=catalog.bad, title="Neu", status=MeasureStatus.IN_PROGRESS
    )

    assert points_of(participant) == {}


def test_return_is_all_or_nothing(
    participant: Participant, catalog: Catalog, measure: Measure
) -> None:
    other = new_person()
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    save_distribution(other, {Target("f", catalog.bad.pk): 50})
    events_before = PointEvent.objects.count()

    # Fehler nach dem Schreiben, aber vor dem Commit: alles wird zurückgerollt.
    with (
        mock.patch("apps.points.returns.transaction.on_commit", side_effect=RuntimeError("weg")),
        pytest.raises(RuntimeError),
    ):
        return_points(measure.facility, measure=measure)

    assert Allocation.objects.filter(facility=catalog.bad).count() == 2
    assert PointEvent.objects.count() == events_before


def test_returned_points_can_be_given_again(
    participant: Participant, catalog: Catalog, measure: Measure
) -> None:
    bad = Target("f", catalog.bad.pk)
    save_distribution(participant, {bad: 100})
    _start(measure)

    save_distribution(participant, {bad: 100})

    assert points_of(participant) == {bad: 100}


def test_distribute_page_lists_returned_points(
    logged_in: Client, participant: Participant, catalog: Catalog, measure: Measure
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    _start(measure)

    content = logged_in.get("/verteilen/").content.decode()

    assert "Wieder frei in den letzten 30 Tagen" in content
    assert "„Dach sanieren“" in content
    assert [c.points for c in recent_changes(participant)] == [30]
