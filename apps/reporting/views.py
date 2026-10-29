"""Öffentliche Seiten: Übersicht und Ergebnisse, mit den eigenen Punkten nur nach Anmeldung."""

from datetime import date

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.access.models import Participant
from apps.access.session import current_participant
from apps.points.models import POINTS_BUDGET
from apps.points.services import points_of, valid_until
from apps.proposals.services import leading_proposals, pending_proposal
from apps.reporting.dashboard import (
    my_points,
    participation_by_week,
    participation_since,
    recent_measures,
    wish_budget,
)
from apps.reporting.export import results_csv
from apps.reporting.map_data import map_payload, results_payload
from apps.reporting.results import build_results
from apps.reporting.statistics import Overview, build_overview


@require_GET
def overview(request: HttpRequest) -> HttpResponse:
    participant = current_participant(request)
    stats = build_overview(points_of(participant) if participant else None)
    results = build_results(stats)
    mine = my_points(stats)
    own_facilities = {p.facility.pk for p in stats.places if p.facility and p.mine > 0}
    return render(
        request,
        "reporting/overview.html",
        {
            "stats": stats,
            "wish": wish_budget(stats, results),
            "participation": participation_by_week(),
            "mine": mine,
            "valid_until": _valid_until(participant),
            "news": recent_measures(own_facilities if participant else None),
            "proposals": leading_proposals(participant),
            "pending": pending_proposal(participant),
            "support_threshold": settings.PROPOSAL_SUPPORT_THRESHOLD,
            "review_days": settings.PROPOSAL_REVIEW_DAYS,
            "map_data": map_payload(stats, results),
            **_map_settings(),
            "budget": POINTS_BUDGET,
            "remaining": mine.free,
        },
    )


@require_GET
def results(request: HttpRequest) -> HttpResponse:
    """Wunsch und Haushalt je Ort; ``?ort=`` wählt die Detailansicht auch ohne JavaScript."""
    outcome = build_results(_overview_for(request))
    return render(
        request,
        "reporting/results.html",
        {
            "results": outcome,
            "selected": outcome.select(request.GET.get("ort")),
            "map_data": results_payload(outcome),
            "now": timezone.localtime(),
            "since": participation_since(),
            "budget": POINTS_BUDGET,
            **_map_settings(),
        },
    )


@require_GET
def results_table(request: HttpRequest) -> HttpResponse:
    """Dieselben Zahlen als CSV; städtische Werte, ohne eigene Punkte."""
    outcome = build_results(build_overview())
    response = HttpResponse(
        results_csv(outcome, settings.CITY_NAME), content_type="text/csv; charset=utf-8"
    )
    response["Content-Disposition"] = 'attachment; filename="stadtstimme-ergebnisse.csv"'
    return response


def _overview_for(request: HttpRequest) -> Overview:
    participant = current_participant(request)
    return build_overview(points_of(participant) if participant else None)


def _valid_until(participant: Participant | None) -> date | None:
    return valid_until(participant) if participant else None


def _map_settings() -> dict[str, str]:
    return {"map_tile_url": settings.MAP_TILE_URL, "map_attribution": settings.MAP_ATTRIBUTION}
