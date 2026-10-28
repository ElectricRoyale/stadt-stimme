"""Dashboard „auf einen Blick“: öffentlich, mit den eigenen Punkten nur nach Anmeldung."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.access.session import current_participant
from apps.points.models import POINTS_BUDGET
from apps.points.services import points_of
from apps.reporting.map_data import map_payload
from apps.reporting.statistics import build_overview


@require_GET
def overview(request: HttpRequest) -> HttpResponse:
    participant = current_participant(request)
    mine = points_of(participant) if participant else None
    stats = build_overview(mine)
    return render(
        request,
        "reporting/overview.html",
        {
            "stats": stats,
            "map_data": map_payload(stats),
            "map_tile_url": settings.MAP_TILE_URL,
            "map_attribution": settings.MAP_ATTRIBUTION,
            "budget": POINTS_BUDGET,
            "remaining": POINTS_BUDGET - stats.mine_used,
        },
    )
