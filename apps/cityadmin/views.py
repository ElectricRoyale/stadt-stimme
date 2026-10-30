"""Verwaltungsseite: was wartet, wie die Beteiligung läuft, Vorschläge entscheiden (ADR-026)."""

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from apps.cityadmin.desk import (
    access_summary,
    answer_tasks,
    facility_ledger,
    proposal_tabs,
    selected_tab,
)
from apps.cityadmin.forms import DecisionForm, SnapshotForm
from apps.cityadmin.snapshot import snapshot_csv
from apps.proposals.board import build_board, item_for
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import DecisionError, decide_proposal, similar_measures
from apps.reporting.dashboard import participation_by_week, participation_since
from apps.reporting.results import build_results
from apps.reporting.statistics import build_overview

View = Callable[..., HttpResponse]


def staff_required(view: View) -> View:
    """Nur Mitarbeitende der Stadt; alle anderen zur Anmeldung der Stadtverwaltung."""

    @wraps(view)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = request.user
        if not (user.is_authenticated and user.is_staff):
            return redirect("access:staff_login")
        return view(request, *args, **kwargs)

    return wrapper


@require_GET
@staff_required
def index(request: HttpRequest) -> HttpResponse:
    board = build_board(None)
    tabs = proposal_tabs(board)
    results = build_results(build_overview())
    tasks = answer_tasks(board)
    return render(
        request,
        "cityadmin/index.html",
        {
            "brand_tag": "Verwaltung",
            "tasks": tasks,
            "overdue": sum(1 for t in tasks if t.days_left < 0),
            "tabs": tabs,
            "tab": selected_tab(tabs, request.GET.get("tab", "")),
            "access": access_summary(),
            "participation": participation_by_week(),
            "since": participation_since(),
            "ledger": facility_ledger(results),
            "fiscal_year": results.fiscal_year,
            "now": timezone.localtime(),
            "support_threshold": settings.PROPOSAL_SUPPORT_THRESHOLD,
            "review_days": settings.PROPOSAL_REVIEW_DAYS,
            "admin_enabled": settings.DEMO_MODE,
            "snapshot_form": SnapshotForm(initial={"datum": timezone.localdate()}),
        },
    )


@require_GET
@staff_required
def snapshot(request: HttpRequest) -> HttpResponse:
    """CSV mit Punkten und Unterstützern je Ziel zum Ende des gewählten Tages (M7, ADR-027)."""
    form = SnapshotForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest("Bitte ein gültiges Datum im Format JJJJ-MM-TT angeben.")
    day = form.cleaned_data["datum"]
    response = HttpResponse(
        snapshot_csv(day, settings.CITY_NAME), content_type="text/csv; charset=utf-8"
    )
    response["Content-Disposition"] = f'attachment; filename="stadtstimme-stichtag-{day}.csv"'
    return response


@require_http_methods(["GET", "POST"])
@staff_required
def decide(request: HttpRequest, pk: int) -> HttpResponse:
    proposal = get_object_or_404(
        Proposal.objects.select_related("category", "facility", "measure"), pk=pk
    )
    is_open = proposal.status == ProposalStatus.OPEN
    form = DecisionForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if not request.user.has_perm("proposals.change_proposal"):
            raise PermissionDenied
        if is_open and form.is_valid():
            try:
                decide_proposal(
                    proposal,
                    accept=form.accept,
                    answer=form.cleaned_data["answer"],
                    measure=form.cleaned_data["measure"],
                )
            except DecisionError as error:
                form.add_error(None, str(error))
            else:
                verb = "angenommen" if form.accept else "abgelehnt"
                messages.success(request, f"{proposal.number} {verb}. Die Antwort ist öffentlich.")
                return redirect(f"{reverse('cityadmin:index')}?tab=entschieden#vorschlaege")
    status = 422 if form.is_bound and form.errors else 200
    return render(
        request,
        "cityadmin/decide.html",
        {
            "brand_tag": "Verwaltung",
            "item": item_for(proposal, None),
            "form": form,
            "is_open": is_open,
            "similar": similar_measures(f"{proposal.title} {proposal.text}")[:1],
            "support_threshold": settings.PROPOSAL_SUPPORT_THRESHOLD,
        },
        status=status,
    )
