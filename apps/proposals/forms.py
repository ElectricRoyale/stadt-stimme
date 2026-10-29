from decimal import Decimal
from typing import Any

from django import forms

from apps.catalog.models import Category, Facility
from apps.proposals.models import TEXT_MAX_LENGTH, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH

WHERE_NONE = "allgemein"
WHERE_PLACE = "bekannt"
WHERE_NEW = "neu"


def _coordinate(label: str, limit: int) -> forms.DecimalField:
    return forms.DecimalField(
        label=label,
        required=False,
        max_digits=9,
        decimal_places=6,
        min_value=Decimal(-limit),
        max_value=Decimal(limit),
        widget=forms.HiddenInput,
    )


class ProposalForm(forms.Form):
    title = forms.CharField(
        label="Was soll die Stadt angehen?",
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        help_text=f"Ein Satz reicht. Zwischen {TITLE_MIN_LENGTH} und {TITLE_MAX_LENGTH} Zeichen.",
        error_messages={
            "required": "Schreib in einem Satz, worum es geht.",
            "min_length": (
                f"Bitte mindestens {TITLE_MIN_LENGTH} Zeichen"
                ", damit andere verstehen, worum es geht."
            ),
        },
    )
    text = forms.CharField(
        label="Warum ist das wichtig?",
        required=False,
        max_length=TEXT_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    category = forms.ModelChoiceField(
        label="Zu welchem Thema gehört es?",
        queryset=Category.objects.order_by("name"),
        widget=forms.RadioSelect,
        empty_label=None,
        error_messages={
            "required": "Wähle ein Thema, damit die richtige Stelle den Vorschlag bekommt."
        },
    )
    where = forms.ChoiceField(
        label="Geht es um einen bestimmten Ort?",
        choices=[
            (WHERE_NONE, "Nein, allgemein"),
            (WHERE_PLACE, "Ja, bekannter Ort"),
            (WHERE_NEW, "Ja, neuer Ort"),
        ],
        initial=WHERE_NONE,
        required=False,
        widget=forms.RadioSelect,
    )
    facility = forms.ModelChoiceField(
        label="Welche Einrichtung?",
        queryset=Facility.objects.select_related("category").order_by("name"),
        required=False,
        empty_label="Bitte wählen",
    )
    latitude = _coordinate("Breitengrad", 90)
    longitude = _coordinate("Längengrad", 180)

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        self._clean_place(data)
        facility, category = data.get("facility"), data.get("category")
        if facility is not None and category is not None and facility.category_id != category.pk:
            self.add_error(
                "facility",
                f"„{facility.name}“ gehört nicht zum Thema „{category.name}“. "
                "Wähle einen Ort aus dem Thema oder „Kein bestimmter Ort“.",
            )
        return data

    def _clean_place(self, data: dict[str, Any]) -> None:
        """Genau eine Art Ort: keiner, eine bekannte Einrichtung oder ein Punkt auf der Karte."""
        where = data.get("where") or WHERE_NONE
        if where == WHERE_NONE and data.get("facility") is not None:
            where = WHERE_PLACE  # ohne JavaScript: gewählte Einrichtung zählt
        data["where"] = where
        if where != WHERE_PLACE:
            data["facility"] = None
        elif data.get("facility") is None:
            self.add_error("facility", "Wähle die Einrichtung oder „Nein, allgemein“.")
        point = data.get("latitude") is not None and data.get("longitude") is not None
        if where != WHERE_NEW:
            data["latitude"] = data["longitude"] = None
        elif not point:
            self.add_error("where", "Tippe auf die Karte, um den Ort zu setzen.")
