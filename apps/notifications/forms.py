from django import forms


class ContactForm(forms.Form):
    email = forms.EmailField(
        label="E-Mail-Adresse",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "inputmode": "email"}),
        error_messages={
            "required": "Bitte gib deine E-Mail-Adresse ein.",
            "invalid": "Das sieht nicht nach einer E-Mail-Adresse aus, z. B. name@example.org.",
        },
    )
