from collections.abc import Iterable
from typing import Any

from django import forms

from apps.points.models import POINTS_BUDGET
from apps.points.services import Target


class DistributionForm(forms.Form):
    """Ein Zahlenfeld je Ziel. Feldname ist der Schlüssel des Ziels, z. B. ``f-3`` oder ``c-1``."""

    def __init__(self, targets: Iterable[Target], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.targets = {target.key: target for target in targets}
        for key in self.targets:
            self.fields[key] = forms.IntegerField(
                min_value=0,
                max_value=POINTS_BUDGET,
                required=False,
                error_messages={
                    "invalid": "Bitte eine ganze Zahl eingeben.",
                    "min_value": "Weniger als 0 Punkte geht nicht.",
                    "max_value": f"Mehr als {POINTS_BUDGET} Punkte geht nicht.",
                },
            )

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        total = sum(value or 0 for value in cleaned.values())
        if total > POINTS_BUDGET:
            raise forms.ValidationError(
                f"Du hast {total} Punkte verteilt, es sind aber nur {POINTS_BUDGET} möglich. "
                f"Nimm {total - POINTS_BUDGET} Punkte zurück."
            )
        return cleaned

    def points(self) -> dict[Target, int]:
        return {target: self.cleaned_data.get(key) or 0 for key, target in self.targets.items()}
