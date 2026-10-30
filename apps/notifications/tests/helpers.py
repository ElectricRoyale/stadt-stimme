import re

from django.core import mail

from apps.access.models import Participant
from apps.notifications import services
from apps.notifications.models import NotificationContact

LINK = re.compile(r"http://testserver(/benachrichtigung/bestaetigen/[^/\s]+/)")


def confirm_path(index: int = -1) -> str:
    match = LINK.search(str(mail.outbox[index].body))
    assert match, mail.outbox[index].body
    return match.group(1)


def confirmed_contact(participant: Participant, email: str) -> NotificationContact:
    services.request_contact(participant, email)
    token = confirm_path().rstrip("/").rsplit("/", 1)[1]
    assert services.confirm(token)
    mail.outbox.clear()
    return NotificationContact.objects.get(participant=participant)
