"""Vorschläge der Bürger und ihre Unterstützungen (ADR-014)."""

from django.core.validators import MinLengthValidator
from django.db import models

from apps.access.models import Participant
from apps.catalog.models import Category, Facility

TITLE_MIN_LENGTH = 8
TITLE_MAX_LENGTH = 80
TEXT_MAX_LENGTH = 600


class ProposalStatus(models.TextChoices):
    SUBMITTED = "eingereicht", "Eingereicht"
    PUBLISHED = "freigegeben", "Freigegeben"
    REJECTED = "abgelehnt", "Abgelehnt"


class Proposal(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="proposals",
        verbose_name="Zugang",
    )
    title = models.CharField(
        "Titel", max_length=TITLE_MAX_LENGTH, validators=[MinLengthValidator(TITLE_MIN_LENGTH)]
    )
    text = models.TextField("Beschreibung", max_length=TEXT_MAX_LENGTH, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="proposals", verbose_name="Thema"
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="proposals",
        verbose_name="Ort",
        null=True,
        blank=True,
    )
    status = models.CharField(
        "Status", max_length=20, choices=ProposalStatus.choices, default=ProposalStatus.SUBMITTED
    )
    created_at = models.DateTimeField("Eingereicht am", auto_now_add=True)

    class Meta:
        verbose_name = "Vorschlag"
        verbose_name_plural = "Vorschläge"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.number} {self.title}"

    @property
    def number(self) -> str:
        return f"V-{self.pk}"

    @property
    def where(self) -> str:
        return self.facility.name if self.facility else "Kein bestimmter Ort"


class Support(models.Model):
    proposal = models.ForeignKey(
        Proposal, on_delete=models.CASCADE, related_name="supports", verbose_name="Vorschlag"
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="supports",
        verbose_name="Zugang",
    )
    created_at = models.DateTimeField("Unterstützt am", auto_now_add=True)

    class Meta:
        verbose_name = "Unterstützung"
        verbose_name_plural = "Unterstützungen"
        constraints = [
            models.UniqueConstraint(fields=["proposal", "participant"], name="support_once"),
        ]

    def __str__(self) -> str:
        return f"Unterstützung für {self.proposal.number}"
