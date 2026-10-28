from django import forms

from apps.access.codes import CODE_LENGTH


class RedeemForm(forms.Form):
    code = forms.CharField(
        label="Dein Code",
        # Großzügig, damit Leerzeichen und Bindestriche beim Abtippen nicht stören.
        max_length=CODE_LENGTH * 2,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "off",
                "autocapitalize": "characters",
                "spellcheck": "false",
                "aria-describedby": "code-hinweis",
            }
        ),
    )
