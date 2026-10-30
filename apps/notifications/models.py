"""Freiwillige E-Mail für Hinweise, getrennt vom Zugang gespeichert (ADR-004)."""

from django.db import models

from apps.access.models import Participant
from apps.notifications.crypto import decrypt, new_token


class NotificationContact(models.Model):
    """E-Mail eines Zugangs. Verschickt wird erst nach dem Double-Opt-in (``confirmed_at``).

    Wird der Zugang gelöscht, verschwindet die Zeile mit (CASCADE, L8).
    """

    participant = models.OneToOneField(
        Participant,
        on_delete=models.CASCADE,
        related_name="notification_contact",
        verbose_name="Zugang",
    )
    email_encrypted = models.TextField("E-Mail (verschlüsselt)", editable=False)
    confirm_token_hash = models.CharField(max_length=64, blank=True, editable=False)
    confirm_sent_at = models.DateTimeField("Bestätigung gesendet", null=True, blank=True)
    confirmed_at = models.DateTimeField("Bestätigt", null=True, blank=True)
    unsubscribe_token = models.CharField(
        max_length=64, unique=True, default=new_token, editable=False
    )
    expiry_warned_at = models.DateTimeField("Verfallswarnung gesendet", null=True, blank=True)
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)

    class Meta:
        verbose_name = "E-Mail für Hinweise"
        verbose_name_plural = "E-Mails für Hinweise"

    def __str__(self) -> str:
        return f"E-Mail von {self.participant}"

    @property
    def email(self) -> str:
        return decrypt(self.email_encrypted)

    @property
    def is_confirmed(self) -> bool:
        return self.confirmed_at is not None
