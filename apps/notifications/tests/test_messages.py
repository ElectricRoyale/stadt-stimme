"""Verfallswarnung und Rückfluss-Mail: nur an bestätigte Adressen, immer mit Abmeldelink."""

from collections.abc import Callable
from datetime import timedelta
from typing import Any
from unittest import mock

import pytest
from django.core import mail
from django.utils import timezone
from pytest_django.fixtures import Settings

from apps.access.models import Participant
from apps.catalog.models import Measure, MeasureStatus
from apps.notifications import services
from apps.notifications.expiry import send_expiry_warnings
from apps.notifications.models import NotificationContact
from apps.notifications.tests.helpers import confirmed_contact
from apps.points.services import Target, save_distribution
from apps.points.tests.conftest import Catalog
from apps.reporting.tests.helpers import new_person

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def site(settings: Settings) -> None:
    settings.SITE_URL = "http://testserver"
    settings.POINTS_EXPIRY_DAYS = 183
    settings.POINTS_EXPIRY_WARNING_DAYS = 14


def _age(participant: Participant, days: int) -> None:
    participant.last_active_at = timezone.now() - timedelta(days=days)
    participant.save(update_fields=["last_active_at"])


def test_warning_once_per_inactivity(participant: Participant, catalog: Catalog) -> None:
    contact = confirmed_contact(participant, "anna@example.org")
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    _age(participant, 170)

    assert send_expiry_warnings() == 1
    assert send_expiry_warnings() == 0

    message = mail.outbox[0]
    assert "verfallen bald" in str(message.subject)
    assert f"/benachrichtigung/abmelden/{contact.unsubscribe_token}/" in str(message.body)
    assert message.extra_headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"

    # Die Warnung galt einer früheren Inaktivität: Wer danach aktiv war und wieder lange
    # wegbleibt, wird erneut gewarnt.
    NotificationContact.objects.update(expiry_warned_at=timezone.now() - timedelta(days=200))
    assert send_expiry_warnings() == 1


@pytest.mark.parametrize("days", [100, 184])
def test_no_warning_outside_the_window(
    participant: Participant, catalog: Catalog, days: int
) -> None:
    confirmed_contact(participant, "anna@example.org")
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    _age(participant, days)

    assert send_expiry_warnings() == 0


def test_no_warning_without_points_or_confirmation(
    participant: Participant, catalog: Catalog
) -> None:
    confirmed_contact(participant, "anna@example.org")
    _age(participant, 170)
    pending = new_person()
    services.request_contact(pending, "ben@example.org")
    save_distribution(pending, {Target("f", catalog.bad.pk): 30})
    _age(pending, 170)
    mail.outbox.clear()

    assert send_expiry_warnings() == 0
    assert mail.outbox == []


def test_return_mail_goes_to_confirmed_supporters_after_commit(
    participant: Participant,
    catalog: Catalog,
    django_capture_on_commit_callbacks: Callable[..., Any],
) -> None:
    confirmed_contact(participant, "anna@example.org")
    unconfirmed = new_person()
    services.request_contact(unconfirmed, "ben@example.org")
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    save_distribution(unconfirmed, {Target("f", catalog.bad.pk): 10})
    mail.outbox.clear()
    measure = Measure.objects.create(external_id="M-1", facility=catalog.bad, title="Dach")

    with django_capture_on_commit_callbacks(execute=True):
        measure.status = MeasureStatus.IN_PROGRESS
        measure.save()

    assert [m.to for m in mail.outbox] == [["anna@example.org"]]
    body = str(mail.outbox[0].body)
    assert "30 Punkte" in body and "„Dach“ bei Hallenbad" in body
    assert "/benachrichtigung/abmelden/" in body


def test_one_failed_mail_does_not_stop_the_others(
    participant: Participant, catalog: Catalog
) -> None:
    other = new_person()
    for person, address in [(participant, "anna@example.org"), (other, "ben@example.org")]:
        confirmed_contact(person, address)
        save_distribution(person, {Target("f", catalog.bad.pk): 30})
        _age(person, 170)

    original = mail.EmailMessage.send
    calls = {"n": 0}

    def flaky(self: mail.EmailMessage, *args: Any, **kwargs: Any) -> int:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("kaputt")
        return original(self, *args, **kwargs)

    with mock.patch.object(mail.EmailMessage, "send", flaky):
        assert send_expiry_warnings() == 1
    assert send_expiry_warnings() == 1  # der fehlgeschlagene kommt beim nächsten Lauf dran


def test_smtp_down_sends_nothing_and_raises_nothing(
    participant: Participant, catalog: Catalog
) -> None:
    confirmed_contact(participant, "anna@example.org")
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    _age(participant, 170)

    with mock.patch(
        "django.core.mail.backends.locmem.EmailBackend.open",
        side_effect=ConnectionRefusedError,
        create=True,
    ):
        assert send_expiry_warnings() == 0
    assert send_expiry_warnings() == 1


def test_failed_warnings_do_not_block_expiry(participant: Participant, catalog: Catalog) -> None:
    from django.core.management import CommandError, call_command

    from apps.points.services import points_of

    save_distribution(participant, {Target("f", catalog.bad.pk): 30})
    _age(participant, 184)

    with (
        mock.patch(
            "apps.notifications.management.commands.send_expiry_warnings.send_expiry_warnings",
            side_effect=RuntimeError("kaputt"),
        ),
        pytest.raises(CommandError, match="send_expiry_warnings"),
    ):
        call_command("run_daily_tasks")

    assert points_of(participant) == {}


def test_done_facility_mail_without_measure(
    participant: Participant,
    catalog: Catalog,
    django_capture_on_commit_callbacks: Callable[..., Any],
) -> None:
    from apps.points.returns import mark_done

    confirmed_contact(participant, "anna@example.org")
    save_distribution(participant, {Target("f", catalog.bad.pk): 30})

    with django_capture_on_commit_callbacks(execute=True):
        mark_done(catalog.bad)

    body = str(mail.outbox[0].body)
    assert "die Stadt hat sich um Hallenbad gekümmert" in body
    assert "30 Punkte" in body
    assert "mach einen Vorschlag" in body and "/vorschlaege/" in body
