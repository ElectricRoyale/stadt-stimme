"""Zugang per Aktivierungscode (ADR-001). Der Klartext eines Codes wird nie gespeichert."""

from django.db import models


class AccessCodeStatus(models.TextChoices):
    ISSUED = "ausgegeben", "ausgegeben"
    REDEEMED = "eingeloest", "eingelöst"
    BLOCKED = "gesperrt", "gesperrt"


class AccessCode(models.Model):
    """Ein gedruckter Code. Die Seriennummer steht auf dem Brief und dient später zum Sperren."""

    code_hash = models.CharField("Hash", max_length=64, unique=True, editable=False)
    batch = models.CharField("Charge", max_length=80)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=AccessCodeStatus.choices,
        default=AccessCodeStatus.ISSUED,
    )
    created_at = models.DateTimeField("Erzeugt", auto_now_add=True)
    redeemed_at = models.DateTimeField("Eingelöst", null=True, blank=True)

    class Meta:
        verbose_name = "Aktivierungscode"
        verbose_name_plural = "Aktivierungscodes"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.serial

    @property
    def serial(self) -> str:
        return f"{self.pk:08d}"


class Participant(models.Model):
    """Pseudonymer Zugang einer Person. Kennt keinen Namen, nur den eingelösten Code."""

    access_code = models.OneToOneField(
        AccessCode,
        on_delete=models.PROTECT,
        related_name="participant",
        verbose_name="Aktivierungscode",
    )
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)
    last_active_at = models.DateTimeField("Zuletzt aktiv")

    class Meta:
        verbose_name = "Zugang"
        verbose_name_plural = "Zugänge"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Zugang {self.pk}"


class FailedAttempt(models.Model):
    """Fehlversuch beim Einlösen, für Rate-Limit und Sperre. Speichert die IP nur als Hash."""

    client_hash = models.CharField("Client (Hash)", max_length=64, db_index=True)
    created_at = models.DateTimeField("Zeitpunkt", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Fehlversuch"
        verbose_name_plural = "Fehlversuche"

    def __str__(self) -> str:
        return f"Fehlversuch {self.created_at:%Y-%m-%d %H:%M}"
