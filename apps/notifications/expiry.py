"""Warnung vor dem Verfall der Punkte (ADR-003, ADR-004)."""

from datetime import timedelta

from django.conf import settings
from django.db.models import Exists, F, OuterRef, Q, QuerySet
from django.urls import reverse
from django.utils import timezone

from apps.notifications.mail import absolute, send_to_contacts
from apps.notifications.models import NotificationContact
from apps.points.models import Allocation
from apps.points.services import expiry_cutoff, valid_until


def due_warnings() -> QuerySet[NotificationContact]:
    """Bestätigte Kontakte mit Punkten, deren Frist in den nächsten Warn-Tagen abläuft und die
    für diese Inaktivität noch keine Warnung bekamen. Wer zurückkommt, wird später neu gewarnt."""
    warn_from = timezone.now() - timedelta(
        days=settings.POINTS_EXPIRY_DAYS - settings.POINTS_EXPIRY_WARNING_DAYS
    )
    has_points = Exists(Allocation.objects.filter(participant_id=OuterRef("participant_id")))
    return (
        NotificationContact.objects.filter(
            has_points,
            confirmed_at__isnull=False,
            participant__last_active_at__lte=warn_from,
            participant__last_active_at__gte=expiry_cutoff(),
        )
        .filter(
            Q(expiry_warned_at__isnull=True)
            | Q(expiry_warned_at__lt=F("participant__last_active_at"))
        )
        .select_related("participant")
    )


def send_expiry_warnings() -> int:
    """Idempotent: ein zweiter Lauf am selben Tag schickt nichts mehr."""
    link = absolute(reverse("points:distribute"))
    sent = send_to_contacts(
        list(due_warnings()),
        "expiry_warning",
        lambda contact: {"valid_until": valid_until(contact.participant), "points_url": link},
    )
    NotificationContact.objects.filter(pk__in=[c.pk for c in sent]).update(
        expiry_warned_at=timezone.now()
    )
    return len(sent)
