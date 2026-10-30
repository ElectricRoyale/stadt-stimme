"""E-Mails zusammenbauen und verschicken. Jede E-Mail an eine bestätigte Adresse trägt einen
Abmeldelink, auch als ``List-Unsubscribe``-Header für Ein-Klick-Abmeldung (RFC 8058)."""

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.urls import reverse

from apps.notifications.models import NotificationContact

logger = logging.getLogger(__name__)


def absolute(path: str) -> str:
    return f"{settings.SITE_URL}{path}"


def _subject(template: str, context: Mapping[str, Any]) -> str:
    rendered = render_to_string(f"notifications/email/{template}_subject.txt", dict(context))
    return " ".join(rendered.split())


def build(
    template: str, to: str, context: Mapping[str, Any], *, unsubscribe_url: str | None = None
) -> EmailMessage:
    full = {**context, "city_name": settings.CITY_NAME, "unsubscribe_url": unsubscribe_url}
    message = EmailMessage(
        subject=_subject(template, full),
        body=render_to_string(f"notifications/email/{template}.txt", full),
        to=[to],
    )
    if unsubscribe_url:
        message.extra_headers = {
            "List-Unsubscribe": f"<{unsubscribe_url}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }
    return message


def unsubscribe_url(contact: NotificationContact) -> str:
    return absolute(reverse("notifications:unsubscribe", args=[contact.unsubscribe_token]))


def send_to_contacts(
    contacts: Iterable[NotificationContact],
    template: str,
    context_for: Any,
) -> list[NotificationContact]:
    """Schickt je bestätigtem Kontakt eine E-Mail über eine SMTP-Verbindung.

    ``context_for(contact)`` liefert den Kontext. Ein Fehler bei einer Adresse stoppt die anderen
    nicht; zurück kommen die Kontakte, deren E-Mail rausging.
    """
    confirmed = [contact for contact in contacts if contact.is_confirmed]
    if not confirmed:
        return []
    connection = get_connection()
    try:
        connection.open()
    except Exception:
        logger.exception(
            "SMTP nicht erreichbar, %s E-Mails %s nicht verschickt", len(confirmed), template
        )
        return []
    sent = []
    try:
        for contact in confirmed:
            message = build(
                template,
                contact.email,
                context_for(contact),
                unsubscribe_url=unsubscribe_url(contact),
            )
            message.connection = connection
            try:
                message.send()
            except Exception:
                logger.exception("E-Mail %s an Kontakt %s fehlgeschlagen", template, contact.pk)
            else:
                sent.append(contact)
    finally:
        connection.close()
    return sent
