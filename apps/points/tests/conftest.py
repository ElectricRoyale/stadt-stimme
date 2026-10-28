from dataclasses import dataclass

import pytest
from django.test import Client
from django.utils import timezone

from apps.access.models import Participant
from apps.access.services import create_codes, redeem_code
from apps.catalog.models import Category, Facility


@dataclass(frozen=True)
class Catalog:
    sport: Category
    bildung: Category
    bad: Facility
    halle: Facility
    schule: Facility


@pytest.fixture
def catalog(db: None) -> Catalog:
    sport = Category.objects.create(name="Sport")
    bildung = Category.objects.create(name="Bildung")
    return Catalog(
        sport=sport,
        bildung=bildung,
        bad=Facility.objects.create(external_id="E-1", name="Hallenbad", category=sport),
        halle=Facility.objects.create(external_id="E-2", name="Sporthalle", category=sport),
        schule=Facility.objects.create(external_id="E-3", name="Grundschule", category=bildung),
    )


@pytest.fixture
def participant(db: None) -> Participant:
    issued = create_codes(1, batch="Test")[0]
    result = redeem_code(issued.code, client="127.0.0.1")
    assert result.participant is not None
    return result.participant


@pytest.fixture
def logged_in(client: Client, participant: Participant) -> Client:
    from apps.access.session import SESSION_KEY

    session = client.session
    session[SESSION_KEY] = participant.pk
    session.save()
    participant.last_active_at = timezone.now()
    participant.save(update_fields=["last_active_at"])
    return client
