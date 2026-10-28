"""Vorschlag machen: Anliegen, Einordnen, Prüfen (Skizze „Vorschlag kombiniert“)."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.access.models import Participant
from apps.access.session import current_participant
from apps.access.views import participant_required
from apps.catalog.models import Facility
from apps.proposals.forms import ProposalForm
from apps.proposals.models import Proposal, ProposalStatus
from apps.proposals.services import (
    DailyLimitError,
    similar_proposals,
    submit_proposal,
    toggle_support,
)

# Zeilen der Prüfansicht in Schritt 3: (Feld, Beschriftung, Schritt zum Ändern).
REVIEW_ROWS = [
    ("title", "Titel", 1),
    ("text", "Beschreibung", 1),
    ("category", "Thema", 2),
    ("where", "Ort", 2),
]


@require_http_methods(["GET", "POST"])
def new(request: HttpRequest) -> HttpResponse:
    """Öffentlich lesbar; einreichen nur mit Zugang."""
    participant = current_participant(request)
    form = ProposalForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if participant is None:
            return redirect("access:redeem")
        if form.is_valid():
            try:
                proposal = submit_proposal(
                    participant,
                    title=form.cleaned_data["title"],
                    text=form.cleaned_data["text"],
                    category=form.cleaned_data["category"],
                    facility=form.cleaned_data["facility"],
                )
            except DailyLimitError as error:
                form.add_error(None, str(error))
            else:
                return redirect("proposals:thanks", pk=proposal.pk)
    status = 422 if form.is_bound and form.errors else 200
    return render(request, "proposals/new.html", _context(form), status=status)


@require_GET
@participant_required
def thanks(request: HttpRequest, participant: Participant, pk: int) -> HttpResponse:
    proposal = get_object_or_404(Proposal, pk=pk, participant=participant)
    return render(request, "proposals/thanks.html", {"proposal": proposal, **_rules()})


@require_GET
def similar(request: HttpRequest) -> JsonResponse:
    viewer = current_participant(request)
    items = similar_proposals(request.GET.get("q", "")[:700], viewer)
    return JsonResponse(
        {
            "items": [
                {
                    "id": item.proposal.pk,
                    "title": item.proposal.title,
                    "supports": item.supports,
                    "supported": item.supported,
                    "own": viewer is not None and item.proposal.participant_id == viewer.pk,
                }
                for item in items
            ]
        }
    )


@require_POST
def support(request: HttpRequest, pk: int) -> JsonResponse:
    participant = current_participant(request)
    if participant is None:
        return JsonResponse({"error": "Bitte melde dich mit deinem Code an."}, status=403)
    proposal = get_object_or_404(Proposal, pk=pk, status=ProposalStatus.PUBLISHED)
    if proposal.participant_id == participant.pk:
        return JsonResponse(
            {"error": "Eigene Vorschläge kannst du nicht unterstützen."}, status=400
        )
    supported = toggle_support(proposal, participant)
    return JsonResponse({"supported": supported, "supports": proposal.supports.count()})


def _context(form: ProposalForm) -> dict[str, object]:
    facilities = Facility.objects.select_related("category").order_by("name")
    return {
        "form": form,
        "review_rows": REVIEW_ROWS,
        "guess_data": [{"id": f.pk, "name": f.name, "category": f.category_id} for f in facilities],
        **_rules(),
    }


def _rules() -> dict[str, int]:
    return {
        "review_days": settings.PROPOSAL_REVIEW_DAYS,
        "support_threshold": settings.PROPOSAL_SUPPORT_THRESHOLD,
    }
