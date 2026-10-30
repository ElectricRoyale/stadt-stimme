"""Code einlösen, Anmeldung der Verwaltung, eigener Bereich, Abmelden. Fachlogik in ``services``."""

from collections.abc import Callable
from functools import wraps

from django.conf import settings
from django.contrib.auth import login as staff_log_in
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.access.forms import RedeemForm
from apps.access.models import Participant
from apps.access.services import (
    RedeemError,
    is_locked_out,
    record_failed_attempt,
    redeem_code,
)
from apps.access.session import current_participant, log_in, log_out

View = Callable[..., HttpResponse]


def participant_required(view: Callable[..., HttpResponse]) -> View:
    """Leitet ohne gültige Sitzung zum Einlösen des Codes um."""

    @wraps(view)
    def wrapper(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        participant = current_participant(request)
        if participant is None:
            return redirect("access:redeem")
        return view(request, participant, *args, **kwargs)

    return wrapper


@require_http_methods(["GET", "POST"])
def redeem(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        if current_participant(request) is not None:
            return redirect("reporting:overview")
        # Der QR-Code auf dem Brief verlinkt mit ?code=…; eingelöst wird erst per Absenden.
        prefilled = request.GET.get("code", "").strip()
        form = RedeemForm(initial={"code": prefilled})
        return render(request, "access/redeem.html", {"form": form, "from_qr": bool(prefilled)})

    form = RedeemForm(request.POST)
    if not form.is_valid():
        return render(request, "access/redeem.html", {"form": form})

    result = redeem_code(form.cleaned_data["code"], client=_client_address(request))
    if result.participant is not None:
        log_in(request, result.participant)
        return redirect("reporting:overview")

    error = result.error or RedeemError.UNKNOWN
    form.add_error("code", error.value)
    status = 429 if error is RedeemError.LOCKED_OUT else 200
    return render(request, "access/redeem.html", {"form": form}, status=status)


STAFF_LOGIN_FAILED = "Benutzername oder Passwort stimmt nicht."


@require_http_methods(["GET", "POST"])
def staff_login(request: HttpRequest) -> HttpResponse:
    """Anmeldung der Stadtverwaltung, führt auf die Verwaltungsseite. Bisher nur im Demo-Modus."""
    enabled = settings.DEMO_MODE
    if enabled and request.user.is_authenticated and request.user.is_staff:
        return redirect("cityadmin:index")
    error, status = None, 200
    if enabled and request.method == "POST":
        client = _client_address(request)
        form = AuthenticationForm(request, data=request.POST)
        if is_locked_out(client):
            error, status = RedeemError.LOCKED_OUT.value, 429
        elif form.is_valid() and form.get_user().is_staff:
            staff_log_in(request, form.get_user())
            return redirect("cityadmin:index")
        else:
            record_failed_attempt(client)
            error = STAFF_LOGIN_FAILED
    context = {
        "username": request.POST.get("username", ""),
        "error": error,
        "enabled": enabled,
        "demo_mode": settings.DEMO_MODE,
    }
    return render(request, "access/staff_login.html", context, status=status)


@require_http_methods(["GET"])
@participant_required
def account(request: HttpRequest, participant: Participant) -> HttpResponse:
    return render(request, "access/account.html", {"participant": participant})


@require_POST
def logout(request: HttpRequest) -> HttpResponse:
    log_out(request)
    return redirect("core:home")


def _client_address(request: HttpRequest) -> str:
    # Hinter einem Reverse Proxy muss dieser die echte Adresse liefern (Betrieb, Phase 6).
    return str(request.META.get("REMOTE_ADDR", "unbekannt"))
