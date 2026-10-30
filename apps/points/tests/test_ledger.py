"""Ereignis-Log: jede Punkteänderung als unveränderliches Ereignis (ADR-027)."""

import pytest
from django.db import DatabaseError, transaction

from apps.access.models import Participant
from apps.points.models import ImmutableEventError, PointEvent, PointEventKind
from apps.points.services import Target, save_distribution, withdraw_all
from apps.points.tests.conftest import Catalog

pytestmark = pytest.mark.django_db


def _events(participant: Participant) -> list[tuple[str, Target, int]]:
    return [
        (e.kind, Target.of(e), e.delta)
        for e in PointEvent.objects.filter(participant=participant).order_by("id")
    ]


def test_saving_writes_only_the_differences(participant: Participant, catalog: Catalog) -> None:
    bad, sport = Target("f", catalog.bad.pk), Target("c", catalog.sport.pk)
    save_distribution(participant, {bad: 30, sport: 20})
    save_distribution(participant, {bad: 10, sport: 20})

    assert _events(participant) == [
        (PointEventKind.GRANTED, sport, 20),
        (PointEventKind.GRANTED, bad, 30),
        (PointEventKind.WITHDRAWN, bad, -20),
    ]


def test_saving_the_same_distribution_writes_nothing(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    assert PointEvent.objects.count() == 1


def test_events_cannot_be_changed_or_deleted(participant: Participant, catalog: Catalog) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    event = PointEvent.objects.get()

    with pytest.raises(ImmutableEventError):
        event.save()
    with pytest.raises(ImmutableEventError):
        event.delete()
    # Auch am ORM vorbei verbietet die Datenbank Änderungen.
    with pytest.raises(DatabaseError), transaction.atomic():
        PointEvent.objects.filter(pk=event.pk).update(delta=99)
    with pytest.raises(DatabaseError), transaction.atomic():
        PointEvent.objects.filter(pk=event.pk).delete()


def test_deleting_a_participant_withdraws_points_and_keeps_the_log(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    participant_id = participant.pk

    participant.delete()

    kinds = list(
        PointEvent.objects.filter(participant_id=participant_id).values_list("kind", "delta")
    )
    assert kinds == [(PointEventKind.GRANTED, 30), (PointEventKind.WITHDRAWN, -30)]


def test_withdraw_all_without_points_is_harmless(participant: Participant) -> None:
    withdraw_all(participant.pk)

    assert not PointEvent.objects.exists()
