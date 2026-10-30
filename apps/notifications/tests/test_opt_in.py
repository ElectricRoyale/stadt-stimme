"""Double-Opt-in, Verschlüsselung und Abmelden (ADR-004)."""

from datetime import timedelta
from unittest import mock

import pytest
from django.core import mail
from django.test import Client
from django.utils import timezone
from pytest_django.fixtures import Settings

from apps.access.models import Participant
from apps.notifications import services
from apps.notifications.models import NotificationContact
from apps.notifications.tests.helpers import confirm_path, confirmed_contact

pytestmark = pytest.mark.django_db
EMAIL = "anna@example.org"


@pytest.fixture(autouse=True)
def site(settings: Settings) -> None:
    settings.SITE_URL = "http://testserver"


def test_signup_sends_link_and_stays_unconfirmed(logged_in: Client) -> None:
    response = logged_in.post("/benachrichtigung/", {"email": EMAIL}, follow=True)

    contact = NotificationContact.objects.get()
    assert contact.confirmed_at is None
    assert mail.outbox[0].to == [EMAIL]
    assert "Wir warten auf deine Bestätigung für" in response.content.decode()
    assert "a•••@example.org" in response.content.decode()


def test_address_is_stored_encrypted(participant: Participant) -> None:
    services.request_contact(participant, EMAIL)

    contact = NotificationContact.objects.get()
    assert EMAIL not in contact.email_encrypted
    assert contact.email == EMAIL


def test_get_does_not_confirm_but_post_does_once(logged_in: Client) -> None:
    logged_in.post("/benachrichtigung/", {"email": EMAIL})
    path = confirm_path()

    page = logged_in.get(path)
    assert "Ja, E-Mail bestätigen" in page.content.decode()
    assert NotificationContact.objects.get().confirmed_at is None

    done = logged_in.post(path)
    assert "E-Mail bestätigt" in done.content.decode()
    assert NotificationContact.objects.get().confirmed_at is not None

    again = logged_in.post(path)
    assert "Link nicht mehr gültig" in again.content.decode()


def test_expired_link_does_not_confirm(participant: Participant, settings: Settings) -> None:
    services.request_contact(participant, EMAIL)
    NotificationContact.objects.update(confirm_sent_at=timezone.now() - timedelta(hours=73))
    token = confirm_path().rstrip("/").rsplit("/", 1)[1]

    assert not services.confirm(token)
    assert NotificationContact.objects.get().confirmed_at is None


def test_new_address_needs_new_confirmation(participant: Participant, settings: Settings) -> None:
    confirmed_contact(participant, EMAIL)
    settings.EMAIL_RESEND_MINUTES = 0

    services.request_contact(participant, "neu@example.org")

    contact = NotificationContact.objects.get()
    assert contact.email == "neu@example.org"
    assert contact.confirmed_at is None


def test_resend_is_rate_limited(logged_in: Client) -> None:
    logged_in.post("/benachrichtigung/", {"email": EMAIL})

    response = logged_in.post("/benachrichtigung/", {"email": EMAIL})

    assert response.status_code == 422
    assert "gerade erst eine Bestätigung" in response.content.decode()
    assert len(mail.outbox) == 1


def test_failed_send_keeps_nothing(logged_in: Client) -> None:
    with mock.patch(
        "django.core.mail.EmailMessage.send", side_effect=OSError("SMTP nicht erreichbar")
    ):
        response = logged_in.post("/benachrichtigung/", {"email": EMAIL})

    assert response.status_code == 422
    assert "ließ sich gerade nicht verschicken" in response.content.decode()
    assert not NotificationContact.objects.exists()


def test_invalid_address_is_rejected(logged_in: Client) -> None:
    response = logged_in.post("/benachrichtigung/", {"email": "keine-adresse"})

    assert response.status_code == 422
    assert not NotificationContact.objects.exists()


def test_settings_need_a_code(client: Client) -> None:
    response = client.get("/benachrichtigung/")

    assert response.status_code == 302
    assert response["Location"] == "/zugang/"


def test_unsubscribe_deletes_address_without_login(
    client: Client, participant: Participant
) -> None:
    contact = confirmed_contact(participant, EMAIL)
    path = f"/benachrichtigung/abmelden/{contact.unsubscribe_token}/"

    assert "Keine E-Mails mehr?" in client.get(path).content.decode()
    assert NotificationContact.objects.exists()

    # Ein-Klick-Abmeldung aus dem Mailprogramm kommt ohne CSRF-Token (RFC 8058).
    csrf_client = Client(enforce_csrf_checks=True)
    response = csrf_client.post(path, {"List-Unsubscribe": "One-Click"})
    assert response.status_code == 200
    assert not NotificationContact.objects.exists()
    assert "Abgemeldet" in csrf_client.post(path).content.decode()


def test_remove_from_settings(logged_in: Client, participant: Participant) -> None:
    confirmed_contact(participant, EMAIL)

    logged_in.post("/benachrichtigung/entfernen/")

    assert not NotificationContact.objects.exists()


def test_deleting_participant_deletes_address(participant: Participant) -> None:
    confirmed_contact(participant, EMAIL)

    participant.delete()

    assert not NotificationContact.objects.exists()
