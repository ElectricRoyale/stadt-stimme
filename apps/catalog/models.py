"""Katalog: Einrichtungen, Gebäude, Maßnahmen und Ausgaben (ADR-002, ADR-006)."""

from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class CategoryColor(models.TextChoices):
    """Die fünf Themenfarben der Design-Tokens (``--ss-cat-<wert>``)."""

    CYAN = "verkehr", "Cyan"
    VIOLET = "bildung", "Violett"
    GREEN = "freizeit", "Grün"
    PINK = "familie", "Pink"
    STONE = "sicherheit", "Stein"
    BLUE = "kultur", "Blau"


# Lucide-Symbol je Themenfarbe, wie im Prototyp (ADR-018). Name steht immer daneben.
COLOR_ICONS: dict[str, str] = {
    CategoryColor.CYAN: "train-front",
    CategoryColor.VIOLET: "graduation-cap",
    CategoryColor.GREEN: "volleyball",
    CategoryColor.PINK: "heart-handshake",
    CategoryColor.STONE: "shield",
    CategoryColor.BLUE: "library-big",
}


# Übliche Themennamen bekommen ihre Farbe aus dem Prototyp (ADR-017), andere reihum.
NAME_COLORS = {
    "bildung": CategoryColor.VIOLET,
    "sport": CategoryColor.GREEN,
    "freizeit": CategoryColor.GREEN,
    "mobilität": CategoryColor.CYAN,
    "verkehr": CategoryColor.CYAN,
    "soziales": CategoryColor.PINK,
    "familie": CategoryColor.PINK,
    "kultur": CategoryColor.BLUE,
    "sicherheit": CategoryColor.STONE,
}


class Category(models.Model):
    """Grobe Einordnung einer Einrichtung (z. B. Sport, Bildung) für Filter und Vergleich.

    Bürger können Punkte auch an ein ganzes Thema geben („… allgemein“, ADR-002).
    """

    name = models.CharField("Name", max_length=80, unique=True)
    color = models.CharField(
        "Farbe",
        max_length=12,
        choices=CategoryColor.choices,
        blank=True,
        help_text="Leer lassen: übliche Themen bekommen ihre Farbe, andere reihum.",
    )

    class Meta:
        verbose_name = "Kategorie"
        verbose_name_plural = "Kategorien"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.color:
            palette = CategoryColor.values
            fallback = palette[Category.objects.count() % len(palette)]
            self.color = NAME_COLORS.get(self.name.strip().lower(), fallback)
        super().save(*args, **kwargs)

    @property
    def icon(self) -> str:
        """Name des Lucide-Symbols für ``partials/icon.html``."""
        return COLOR_ICONS.get(self.color, "map-pin")


class Facility(models.Model):
    """Öffentliche Einrichtung der Kommune; trägt Maßnahmen.

    „Erledigt“ heißt: Die Stadt hat sich um den aktuellen Wunsch gekümmert, die Punkte sind
    zurück bei den Unterstützern (ADR-029). Die Einrichtung bleibt wählbar.
    """

    external_id = models.CharField(
        "Externe ID",
        max_length=64,
        unique=True,
        help_text="Schlüssel aus dem Quellsystem; macht den CSV-Import wiederholbar.",
    )
    name = models.CharField("Name", max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="facilities",
        verbose_name="Kategorie",
    )
    address = models.CharField("Adresse", max_length=200, blank=True)
    description = models.TextField("Kurzbeschreibung", blank=True)
    latitude = models.DecimalField(
        "Breitengrad",
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="Für die Karte, z. B. 50.868600. Ohne Koordinaten fehlt die Einrichtung dort.",
    )
    longitude = models.DecimalField(
        "Längengrad",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    done_at = models.DateTimeField(
        "Zuletzt erledigt",
        null=True,
        blank=True,
        editable=False,
        help_text="Gesetzt über „Erledigt“ auf der Verwaltungsseite.",
    )
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "Einrichtung"
        verbose_name_plural = "Einrichtungen"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def has_location(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def clean(self) -> None:
        super().clean()
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError("Breiten- und Längengrad nur zusammen angeben.")


class Building(models.Model):
    """Gebäude oder Standort einer Einrichtung, z. B. Hauptgebäude und Turnhalle einer Schule.

    Optional: Eine Einrichtung mit nur einem Gebäude braucht keinen Eintrag. Verglichen wird
    weiter pro Einrichtung (ADR-006); das Gebäude präzisiert nur, wo eine Maßnahme ansetzt.
    """

    external_id = models.CharField(
        "Externe ID",
        max_length=64,
        unique=True,
        help_text="Schlüssel aus dem Quellsystem; macht den CSV-Import wiederholbar.",
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="buildings",
        verbose_name="Einrichtung",
    )
    name = models.CharField("Name", max_length=200)
    address = models.CharField("Adresse", max_length=200, blank=True)
    description = models.TextField("Kurzbeschreibung", blank=True)
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "Gebäude"
        verbose_name_plural = "Gebäude"
        ordering = ["facility__name", "name"]

    def __str__(self) -> str:
        return f"{self.facility}: {self.name}"


class MeasureStatus(models.TextChoices):
    OPEN = "offen", "offen"
    DECIDED = "beschlossen", "beschlossen"
    IN_PROGRESS = "in_umsetzung", "in Umsetzung"
    COMPLETED = "abgeschlossen", "abgeschlossen"
    REJECTED = "verworfen", "verworfen"


class Measure(models.Model):
    """Konkretes Vorhaben an genau einer Einrichtung; Bürger vergeben Punkte darauf."""

    external_id = models.CharField(
        "Externe ID",
        max_length=64,
        unique=True,
        help_text="Schlüssel aus dem Quellsystem; macht den CSV-Import wiederholbar.",
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="measures",
        verbose_name="Einrichtung",
    )
    building = models.ForeignKey(
        Building,
        on_delete=models.PROTECT,
        related_name="measures",
        verbose_name="Gebäude",
        null=True,
        blank=True,
        help_text="Optional; muss zur gewählten Einrichtung gehören.",
    )
    title = models.CharField("Titel", max_length=200)
    description = models.TextField("Beschreibung", blank=True)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=MeasureStatus.choices,
        default=MeasureStatus.OPEN,
    )
    created_at = models.DateTimeField("Angelegt", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert", auto_now=True)

    class Meta:
        verbose_name = "Maßnahme"
        verbose_name_plural = "Maßnahmen"
        ordering = ["facility__name", "title"]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        super().clean()
        building = self.building
        if building is not None and self.facility_id and building.facility_id != self.facility_id:
            raise ValidationError({"building": "Das Gebäude gehört zu einer anderen Einrichtung."})


class ExpenditureKind(models.TextChoices):
    PLAN = "plan", "Plan"
    ACTUAL = "ist", "Ist"


class Expenditure(models.Model):
    """Ausgabe einer Einrichtung in einem Haushaltsjahr, optional einer Maßnahme zugeordnet."""

    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name="expenditures",
        verbose_name="Einrichtung",
    )
    measure = models.ForeignKey(
        Measure,
        on_delete=models.PROTECT,
        related_name="expenditures",
        verbose_name="Maßnahme",
        null=True,
        blank=True,
    )
    fiscal_year = models.PositiveSmallIntegerField("Haushaltsjahr")
    amount = models.DecimalField("Betrag (EUR)", max_digits=14, decimal_places=2)
    kind = models.CharField("Art", max_length=10, choices=ExpenditureKind.choices)
    source = models.CharField("Quelle", max_length=200)
    as_of = models.DateField("Datenstand")

    class Meta:
        verbose_name = "Ausgabe"
        verbose_name_plural = "Ausgaben"
        ordering = ["-fiscal_year", "facility__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["facility", "measure", "fiscal_year", "kind"],
                nulls_distinct=False,
                name="expenditure_unique_per_year_and_kind",
                violation_error_message=(
                    "Für diese Einrichtung, Maßnahme, Jahr und Art gibt es bereits eine Ausgabe."
                ),
            ),
            models.CheckConstraint(
                condition=Q(amount__gte=0),
                name="expenditure_amount_not_negative",
                violation_error_message="Der Betrag darf nicht negativ sein.",
            ),
            models.CheckConstraint(
                condition=Q(fiscal_year__gte=2000) & Q(fiscal_year__lte=2100),
                name="expenditure_fiscal_year_plausible",
                violation_error_message="Das Haushaltsjahr muss zwischen 2000 und 2100 liegen.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.facility} {self.fiscal_year} ({self.get_kind_display()})"

    def clean(self) -> None:
        super().clean()
        measure = self.measure
        if measure is not None and self.facility_id and measure.facility_id != self.facility_id:
            raise ValidationError({"measure": "Die Maßnahme gehört zu einer anderen Einrichtung."})
