from typing import Any

from django import forms

from apps.catalog.models import Category, Facility
from apps.proposals.models import TEXT_MAX_LENGTH, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH

WHERE_NONE = "none"
WHERE_PLACE = "place"


class ProposalForm(forms.Form):
    title = forms.CharField(
        label="Titel",
        min_length=TITLE_MIN_LENGTH,
        max_length=TITLE_MAX_LENGTH,
        help_text="Was soll die Stadt angehen? In einem kurzen Satz.",
        error_messages={
            "required": "Bitte gib einen Titel ein.",
            "min_length": f"Bitte gib einen Titel mit mindestens {TITLE_MIN_LENGTH} Zeichen ein.",
        },
    )
    text = forms.CharField(
        label="Beschreibung",
        required=False,
        max_length=TEXT_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Was stört dich, was fehlt, für wen ist es wichtig?",
    )
    category = forms.ModelChoiceField(
        label="Zu welchem Thema gehört es?",
        queryset=Category.objects.order_by("name"),
        widget=forms.RadioSelect,
        empty_label=None,
        error_messages={"required": "Bitte wähle ein Thema."},
    )
    where = forms.ChoiceField(
        label="Geht es um einen bestimmten Ort?",
        choices=[
            (WHERE_NONE, "Nein, allgemein"),
            (WHERE_PLACE, "Ja, ein bekannter Ort"),
        ],
        initial=WHERE_NONE,
        widget=forms.RadioSelect,
    )
    facility = forms.ModelChoiceField(
        label="Welcher Ort?",
        queryset=Facility.objects.select_related("category").order_by("name"),
        widget=forms.RadioSelect,
        required=False,
        empty_label=None,
    )

    def clean(self) -> dict[str, Any]:
        data = super().clean() or {}
        if data.get("where") != WHERE_PLACE:
            data["facility"] = None
        elif data.get("facility") is None:
            self.add_error("facility", "Bitte wähle einen Ort oder stell „Nein, allgemein“ ein.")
        return data
