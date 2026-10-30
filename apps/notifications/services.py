"""E-Mail für Hinweise eintragen, bestätigen (Double-Opt-in), abmelden (ADR-004)."""

import logging
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.access.models import Participant
from apps.notifications.crypto import encrypt, new_token, token_hash
from apps.notifications.mail import absolute, build
from apps.notifications.models import NotificationContact

logger = logging.getLogger(__name__)


class ContactError(Exception):
    pass


class TooSoonError(ContactError):
    def __init__(self) -> None:
        super().__init__(
            "Wir haben dir gerade erst eine Bestätigung geschickt. Bitte schau in dein Postfach "
            f"oder versuche es in {settings.EMAIL_RESEND_MINUTES} Minuten erneut."
        )


class SendFailedError(ContactError):
    def __init__(self) -> None:
        super().__init__(
            "Die Bestätigung ließ sich gerade nicht verschicken. Bitte versuche es später erneut."
        )


class ContactState(Enum):
    NONE = "keine"
    PENDING = "offen"
    CONFIRMED = "bestaetigt"


@dataclass(frozen=True)
class ContactView:
    state: ContactState
    masked_email: str = ""


def mask(email: str) -> str:
    """„p•••@example.org“: zeigt, welche Adresse es ist, ohne sie ganz auszuschreiben."""
    local, _, domain = email.partition("@")
    return f"{local[:1]}•••@{domain}"


def contact_of(participant: Participant) -> ContactView:
    contact = NotificationContact.objects.filter(participant=participant).first()
    if contact is None:
        return ContactView(ContactState.NONE)
    state = ContactState.CONFIRMED if contact.is_confirmed else ContactState.PENDING
    return ContactView(state, mask(contact.email))


def request_contact(participant: Participant, email: str) -> None:
    """Speichert die Adresse unbestätigt und schickt den Bestätigungslink.

    Eine neue Adresse ersetzt die alte; bis zur Bestätigung geht keine Benachrichtigung raus.
    Scheitert der Versand, bleibt alles wie vorher.
    """
    now = timezone.now()
    with transaction.atomic():
        Participant.objects.select_for_update().filter(pk=participant.pk).get()
        contact = NotificationContact.objects.filter(participant=participant).first()
        cooldown = timedelta(minutes=settings.EMAIL_RESEND_MINUTES)
        if contact and contact.confirm_sent_at and now - contact.confirm_sent_at < cooldown:
            raise TooSoonError
        contact = contact or NotificationContact(participant=participant)
        token = new_token()
        contact.email_encrypted = encrypt(email)
        contact.confirm_token_hash = token_hash(token)
        contact.confirm_sent_at = now
        contact.confirmed_at = None
        contact.unsubscribe_token = new_token()
        contact.expiry_warned_at = None
        contact.save()

        link = absolute(reverse("notifications:confirm", args=[token]))
        message = build("confirm", email, {"confirm_url": link, "hours": _confirm_hours()})
        try:
            message.send()
        except Exception as error:
            logger.exception("Bestätigungsmail für Kontakt %s fehlgeschlagen", contact.pk)
            raise SendFailedError from error


def _confirm_hours() -> int:
    return int(settings.EMAIL_CONFIRM_HOURS)


def pending_for(token: str) -> NotificationContact | None:
    """Unbestätigter Kontakt zum Link, solange der Link gilt."""
    valid_since = timezone.now() - timedelta(hours=_confirm_hours())
    return NotificationContact.objects.filter(
        confirm_token_hash=token_hash(token),
        confirmed_at__isnull=True,
        confirm_sent_at__gte=valid_since,
    ).first()


def confirm(token: str) -> bool:
    """Double-Opt-in abschließen. Ein Link funktioniert genau einmal."""
    with transaction.atomic():
        contact = pending_for(token)
        if contact is None:
            return False
        contact.confirmed_at = timezone.now()
        contact.confirm_token_hash = ""
        contact.save(update_fields=["confirmed_at", "confirm_token_hash"])
    return True


def unsubscribe(token: str) -> bool:
    """Löscht die Adresse vollständig. Wiederholtes Abmelden ist harmlos."""
    if not token:
        return False
    deleted, _ = NotificationContact.objects.filter(unsubscribe_token=token).delete()
    return deleted > 0


def remove_contact(participant: Participant) -> None:
    NotificationContact.objects.filter(participant=participant).delete()
