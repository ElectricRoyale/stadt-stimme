"""Vorschläge: Weg aller Vorschläge, Liste und „Vorschlag machen“ auf einer Seite (ADR-016)."""

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.access.models import Participant
from apps.access.session import current_participant
from apps.catalog.models import Facility
from apps.proposals.board import Board, Item, Stage, build_board, item_for
from apps.proposals.forms import ProposalForm
from apps.proposals.models import (
    TEXT_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    Proposal,
    ProposalStatus,
)
from apps.proposals.services import (
    DailyLimitError,
    similar_measures,
    similar_proposals,
    submit_proposal,
    toggle_support,
)


@require_http_methods(["GET", "POST"])
def index(request: HttpRequest) -> HttpResponse:
    """Öffentlich lesbar; einreichen und unterstützen nur mit Zugang."""
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
                    point=_point(form.cleaned_data),
                )
            except DailyLimitError as error:
                form.add_error(None, str(error))
            else:
                return redirect(
                    f"{reverse('proposals:index')}?eingereicht={proposal.pk}#vorschlag-neu"
                )
    status = 422 if form.is_bound and form.errors else 200
    board = build_board(participant)
    return render(
        request,
        "proposals/index.html",
        _context(request, form, board, participant),
        status=status,
    )


@require_GET
def similar(request: HttpRequest) -> JsonResponse:
    viewer = current_participant(request)
    query = request.GET.get("q", "")[:700]
    proposals = [
        Item(
            s.proposal,
            s.supports,
            s.supported,
            viewer is not None and s.proposal.participant_id == viewer.pk,
        )
        for s in similar_proposals(query, viewer)
    ]
    give = reverse("points:distribute")
    return JsonResponse(
        {
            "measures": [
                {
                    "title": m.title,
                    "facility": m.facility.name,
                    "url": f"{give}#ziel-f-{m.facility_id}",
                }
                for m in similar_measures(query)
            ],
            "items": [_item_json(item, viewer) for item in proposals],
        }
    )


@require_POST
def support(request: HttpRequest, pk: int) -> JsonResponse:
    participant = current_participant(request)
    if participant is None:
        return JsonResponse({"error": "Bitte melde dich mit deinem Code an."}, status=403)
    proposal = get_object_or_404(Proposal, pk=pk, status=ProposalStatus.OPEN)
    if proposal.participant_id == participant.pk:
        return JsonResponse(
            {"error": "Eigene Vorschläge kannst du nicht unterstützen."}, status=400
        )
    supported = toggle_support(proposal, participant)
    item = item_for(proposal, participant)
    return JsonResponse(
        {
            "supported": supported,
            "supports": item.supports,
            "sentence": item.sentence,
            "progress": item.progress,
            "stage": item.stage.value,
            "stageLabel": item.stage.label,
        }
    )


def _item_json(item: Item, viewer: Participant | None) -> dict[str, Any]:
    return {
        "id": item.proposal.pk,
        "title": item.proposal.title,
        "supports": item.supports,
        "supported": item.supported,
        "own": item.own,
        "stage": item.stage.value,
        "stageLabel": item.stage.label,
        "canSupport": viewer is not None and item.can_support,
    }


def _context(
    request: HttpRequest, form: ProposalForm, board: Board, participant: Participant | None
) -> dict[str, Any]:
    sent = _sent(request, board)
    wanted = request.GET.get("schritt", "")
    selected_stage = wanted if wanted in {s.value for s in Stage} else ""
    return {
        "form": form,
        "board": board,
        "items": [i for i in board.visible if not selected_stage or i.stage == selected_stage],
        "selected_stage": selected_stage,
        "stages": list(Stage),
        "sent": sent,
        "facilities": Facility.objects.select_related("category").order_by("name"),
        "place_bounds": _place_bounds(),
        "categories": form.fields["category"].queryset,  # type: ignore[attr-defined]
        "now": timezone.localtime(),
        "title_min": TITLE_MIN_LENGTH,
        "title_max": TITLE_MAX_LENGTH,
        "text_max": TEXT_MAX_LENGTH,
        "support_threshold": settings.PROPOSAL_SUPPORT_THRESHOLD,
        "per_day": settings.PROPOSALS_PER_DAY,
    }


def _place_bounds() -> list[list[float]]:
    """Bekannte Orte, damit die Karte für „Ja, neuer Ort“ auf der Stadt startet."""
    located = Facility.objects.exclude(latitude=None).exclude(longitude=None)
    return [[float(f.latitude), float(f.longitude)] for f in located]  # type: ignore[arg-type]


def _point(data: dict[str, Any]) -> tuple[Decimal, Decimal] | None:
    lat, lng = data.get("latitude"), data.get("longitude")
    return (lat, lng) if lat is not None and lng is not None else None


def _sent(request: HttpRequest, board: Board) -> Item | None:
    """Gerade eingereichter eigener Vorschlag (nach dem Weiterleiten)."""
    key = request.GET.get("eingereicht", "")
    return next((i for i in board.mine if str(i.proposal.pk) == key), None)
