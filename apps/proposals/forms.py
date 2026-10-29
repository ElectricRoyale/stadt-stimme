from typing import Any

from django import forms

from apps.catalog.models import Category, Facility
from apps.proposals.models import TEXT_MAX_LENGTH, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH


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
    facility = forms.ModelChoiceField(
        label="Betrifft es eine bestimmte Einrichtung?",
        queryset=Facility.objects.select_related("category").order_by("name"),
        required=False,
        empty_label="Kein bestimmter Ort",
    )

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        facility, category = data.get("facility"), data.get("category")
        if facility is not None and category is not None and facility.category_id != category.pk:
            self.add_error(
                "facility",
                f"„{facility.name}“ gehört nicht zum Thema „{category.name}“. "
                "Wähle einen Ort aus dem Thema oder „Kein bestimmter Ort“.",
            )
        return data
