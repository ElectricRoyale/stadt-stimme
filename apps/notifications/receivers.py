from collections import defaultdict
from typing import Any

from django.dispatch import receiver
from django.urls import reverse

from apps.catalog.models import Measure
from apps.notifications.mail import absolute, send_to_contacts
from apps.notifications.models import NotificationContact
from apps.points.returns import ReturnedPoints
from apps.points.signals import points_returned


@receiver(points_returned)
def _notify_returned(
    sender: Any, returns: list[ReturnedPoints], measure: Measure, **kwargs: Any
) -> None:
    """Läuft nach dem Commit des Rückflusses; nur an bestätigte Adressen (ADR-004)."""
    points: dict[int, int] = defaultdict(int)
    for item in returns:
        points[item.participant_id] += item.points
    contacts = NotificationContact.objects.filter(
        participant_id__in=points, confirmed_at__isnull=False
    )
    link = absolute(reverse("points:distribute"))
    send_to_contacts(
        list(contacts),
        "points_returned",
        lambda contact: {
            "points": points[contact.participant_id],
            "facility": measure.facility.name,
            "measure": measure.title,
            "points_url": link,
        },
    )
