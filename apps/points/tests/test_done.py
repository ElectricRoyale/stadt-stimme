"""Erledigte Einrichtungen fehlen in „Punkte verteilen“ (ADR-029)."""

import pytest
from django.test import Client
from django.utils import timezone

from apps.access.models import Participant
from apps.catalog.models import Facility
from apps.points.returns import mark_done
from apps.points.services import DoneFacilityError, Target, points_of, save_distribution
from apps.points.tests.conftest import Catalog

pytestmark = pytest.mark.django_db


def test_done_facility_disappears_from_the_list(
    logged_in: Client, participant: Participant, catalog: Catalog
) -> None:
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    mark_done(catalog.bad)

    content = logged_in.get("/verteilen/").content.decode()
    assert f'name="f-{catalog.bad.pk}"' not in content
    assert f'name="f-{catalog.halle.pk}"' in content
    assert "weil die Stadt sich darum gekümmert hat" in content


def test_stale_form_cannot_give_points_to_a_done_facility(
    participant: Participant, catalog: Catalog
) -> None:
    Facility.objects.filter(pk=catalog.bad.pk).update(done_at=timezone.now())

    with pytest.raises(DoneFacilityError, match="Hallenbad"):
        save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    assert points_of(participant) == {}


def test_reopened_facility_is_back(logged_in: Client, catalog: Catalog) -> None:
    mark_done(catalog.bad)
    catalog.bad.refresh_from_db()

    catalog.bad.reopen()

    assert f'name="f-{catalog.bad.pk}"' in logged_in.get("/verteilen/").content.decode()
