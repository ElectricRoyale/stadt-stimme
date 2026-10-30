"""Verfall nach ADR-003 mit Ereignis „verfallen“; der tägliche Lauf ist idempotent."""

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.access.models import Participant
from apps.access.services import active_participant
from apps.points.models import PointEvent, PointEventKind
from apps.points.services import Target, expire_points, points_of, save_distribution
from apps.points.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


def _age(participant: Participant, days: int) -> None:
    participant.last_active_at = timezone.now() - timedelta(days=days)
    participant.save(update_fields=["last_active_at"])


def _expired_events() -> list[tuple[int, int]]:
    events = PointEvent.objects.filter(kind=PointEventKind.EXPIRED).order_by("id")
    return [(e.participant_id, e.delta) for e in events]


def test_expiry_writes_events_and_is_idempotent(participant: Participant, catalog: Catalog) -> None:
    active = new_person()
    save_distribution(
        participant, {Target("f", catalog.bad.pk): 30, Target("c", catalog.sport.pk): 20}
    )
    save_distribution(active, {Target("f", catalog.bad.pk): 40})
    _age(participant, 184)

    assert expire_points() == 2
    assert expire_points() == 0

    assert points_of(participant) == {}
    assert points_of(active) == {Target("f", catalog.bad.pk): 40}
    assert sorted(_expired_events()) == [(participant.pk, -30), (participant.pk, -20)]


def test_returning_after_the_deadline_expires_with_events(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    _age(participant, 200)

    active_participant(participant.pk)

    assert points_of(participant) == {}
    assert _expired_events() == [(participant.pk, -30)]


def test_daily_command_runs_warnings_and_expiry(participant: Participant, catalog: Catalog) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    _age(participant, 184)
    out = StringIO()

    call_command("run_daily_tasks", stdout=out)
    call_command("run_daily_tasks", stdout=out)

    lines = out.getvalue().splitlines()
    assert lines == [
        "0 Verfallswarnungen verschickt.",
        "1 verfallene Punktevergaben entzogen.",
        "0 Verfallswarnungen verschickt.",
        "0 verfallene Punktevergaben entzogen.",
    ]
    assert len(_expired_events()) == 1
