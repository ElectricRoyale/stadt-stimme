from datetime import timedelta

import pytest
from django.utils import timezone
from pytest_django.fixtures import Settings

from apps.access.models import Participant
from apps.access.services import active_participant
from apps.points.models import Allocation
from apps.points.services import (
    BudgetExceededError,
    Target,
    active_allocations,
    expire_points,
    points_of,
    save_distribution,
)
from apps.points.tests.conftest import Catalog

pytestmark = pytest.mark.django_db


def _age(participant: Participant, days: int) -> None:
    participant.last_active_at = timezone.now() - timedelta(days=days)
    participant.save(update_fields=["last_active_at"])


def test_save_distribution_stores_facility_and_theme(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(
        participant, {Target("f", catalog.bad.pk): 30, Target("c", catalog.sport.pk): 20}
    )

    assert points_of(participant) == {
        Target("f", catalog.bad.pk): 30,
        Target("c", catalog.sport.pk): 20,
    }


def test_save_distribution_replaces_previous_and_drops_zero(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    save_distribution(
        participant, {Target("f", catalog.bad.pk): 0, Target("f", catalog.schule.pk): 10}
    )

    assert points_of(participant) == {Target("f", catalog.schule.pk): 10}


def test_save_distribution_allows_exactly_the_budget(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(
        participant, {Target("f", catalog.bad.pk): 60, Target("f", catalog.schule.pk): 40}
    )

    assert sum(points_of(participant).values()) == 100


def test_save_distribution_rejects_more_than_budget(
    participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 10})

    with pytest.raises(BudgetExceededError):
        save_distribution(
            participant, {Target("f", catalog.bad.pk): 60, Target("f", catalog.schule.pk): 41}
        )

    assert points_of(participant) == {Target("f", catalog.bad.pk): 10}


def test_expired_points_do_not_count(
    participant: Participant, catalog: Catalog, settings: Settings
) -> None:
    settings.POINTS_EXPIRY_DAYS = 183
    save_distribution(participant, {Target("f", catalog.bad.pk): 10})
    assert active_allocations().count() == 1

    _age(participant, 184)

    assert active_allocations().count() == 0


def test_expire_points_deletes_only_inactive(
    participant: Participant, catalog: Catalog, settings: Settings
) -> None:
    settings.POINTS_EXPIRY_DAYS = 183
    save_distribution(participant, {Target("f", catalog.bad.pk): 10})
    assert expire_points() == 0

    _age(participant, 184)

    assert expire_points() == 1
    assert not Allocation.objects.exists()


def test_returning_after_expiry_starts_with_full_budget(
    participant: Participant, catalog: Catalog, settings: Settings
) -> None:
    settings.POINTS_EXPIRY_DAYS = 183
    save_distribution(participant, {Target("f", catalog.bad.pk): 10})
    _age(participant, 184)

    active_participant(participant.pk)

    assert points_of(participant) == {}


def test_returning_within_period_keeps_points(
    participant: Participant, catalog: Catalog, settings: Settings
) -> None:
    settings.POINTS_EXPIRY_DAYS = 183
    save_distribution(participant, {Target("f", catalog.bad.pk): 10})
    _age(participant, 30)

    active_participant(participant.pk)

    assert points_of(participant) == {Target("f", catalog.bad.pk): 10}
