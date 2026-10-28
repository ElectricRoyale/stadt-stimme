"""Öffentliche Seiten: Übersicht und Ergebnisse, mit den eigenen Punkten nur nach Anmeldung."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.access.session import current_participant
from apps.points.models import POINTS_BUDGET
from apps.points.services import points_of
from apps.reporting.map_data import map_payload, results_payload
from apps.reporting.results import build_results
from apps.reporting.statistics import Overview, build_overview


@require_GET
def overview(request: HttpRequest) -> HttpResponse:
    stats = _overview_for(request)
    return render(
        request,
        "reporting/overview.html",
        {
            "stats": stats,
            "map_data": map_payload(stats),
            **_map_settings(),
            "budget": POINTS_BUDGET,
            "remaining": POINTS_BUDGET - stats.mine_used,
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
            "map_data": results_payload(outcome, reverse("points:distribute")),
            **_map_settings(),
        },
    )


def _overview_for(request: HttpRequest) -> Overview:
    participant = current_participant(request)
    return build_overview(points_of(participant) if participant else None)


def _map_settings() -> dict[str, str]:
    return {"map_tile_url": settings.MAP_TILE_URL, "map_attribution": settings.MAP_ATTRIBUTION}
