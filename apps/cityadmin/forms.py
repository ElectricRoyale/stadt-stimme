from django import forms

from apps.catalog.models import Measure
from apps.proposals.models import TEXT_MAX_LENGTH
from apps.proposals.services import ANSWER_MIN_LENGTH

ACCEPT, REJECT = "annehmen", "ablehnen"


class MeasureChoice(forms.ModelChoiceField):  # type: ignore[type-arg]
    def label_from_instance(self, obj: Measure) -> str:
        return f"{obj.title} · {obj.facility.name}"


class DecisionForm(forms.Form):
    verdict = forms.ChoiceField(
        label="Entscheidung",
        choices=[(ACCEPT, "Annehmen"), (REJECT, "Ablehnen")],
        widget=forms.RadioSelect,
        error_messages={"required": "Bitte wähle Annehmen oder Ablehnen."},
    )
    answer = forms.CharField(
        label="Antwort der Stadt (öffentlich)",
        min_length=ANSWER_MIN_LENGTH,
        max_length=TEXT_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 5}),
        error_messages={
            "required": "Bitte begründe die Entscheidung.",
            "min_length": f"Bitte mindestens {ANSWER_MIN_LENGTH} Zeichen, damit die "
            "Entscheidung nachvollziehbar ist.",
        },
    )
    measure = MeasureChoice(
        label="Verknüpfte Maßnahme (freiwillig)",
        queryset=Measure.objects.select_related("facility").order_by("facility__name", "title"),
        required=False,
        empty_label="Keine Maßnahme",
    )

    def clean(self) -> dict[str, object]:
        data = super().clean() or {}
        if data.get("verdict") == REJECT:
            data["measure"] = None
        return data

    @property
    def accept(self) -> bool:
        return bool(self.cleaned_data.get("verdict") == ACCEPT)


class SnapshotForm(forms.Form):
    datum = forms.DateField(
        label="Datum",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"required": "Bitte ein Datum wählen.", "invalid": "Kein gültiges Datum."},
    )
