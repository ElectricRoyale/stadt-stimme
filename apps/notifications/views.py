"""E-Mail für Hinweise: eintragen, bestätigen, abmelden. Ohne JavaScript nutzbar (ADR-004)."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from apps.access.models import Participant
from apps.access.views import participant_required
from apps.notifications import services
from apps.notifications.forms import ContactForm


@require_http_methods(["GET", "POST"])
@participant_required
def settings_page(request: HttpRequest, participant: Participant) -> HttpResponse:
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            services.request_contact(participant, form.cleaned_data["email"])
        except services.ContactError as error:
            form.add_error(None, str(error))
        else:
            messages.success(
                request, "Fast geschafft: Bitte bestätige den Link, den wir dir geschickt haben."
            )
            return redirect("notifications:settings")
    status = 422 if form.is_bound and form.errors else 200
    context = {"form": form, "contact": services.contact_of(participant)}
    return render(request, "notifications/settings.html", context, status=status)


@require_POST
@participant_required
def remove(request: HttpRequest, participant: Participant) -> HttpResponse:
    services.remove_contact(participant)
    messages.success(request, "Deine E-Mail-Adresse ist gelöscht.")
    return redirect("notifications:settings")


@require_http_methods(["GET", "POST"])
def confirm(request: HttpRequest, token: str) -> HttpResponse:
    """GET zeigt nur einen Knopf: Link-Vorschauen in Mailprogrammen bestätigen sonst mit."""
    if request.method == "POST":
        done = services.confirm(token)
        return render(
            request, "notifications/confirm.html", {"done": done, "valid": done}, status=200
        )
    valid = services.pending_for(token) is not None
    return render(request, "notifications/confirm.html", {"done": False, "valid": valid})


@csrf_exempt  # Ein-Klick-Abmeldung aus dem Mailprogramm (RFC 8058); das Token ist der Schutz.
@require_http_methods(["GET", "POST"])
def unsubscribe(request: HttpRequest, token: str) -> HttpResponse:
    done = request.method == "POST" and services.unsubscribe(token)
    return render(
        request,
        "notifications/unsubscribe.html",
        {"done": done, "posted": request.method == "POST"},
    )
