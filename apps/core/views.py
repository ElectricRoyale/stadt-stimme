"""Querschnittliche Seiten: Einstieg und Health-Check."""

import logging

from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from apps.access.session import current_participant

logger = logging.getLogger(__name__)


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """Kein eigener Einstieg: Angemeldete sehen die Übersicht, alle anderen geben den Code ein."""
    if current_participant(request) is not None:
        return redirect("reporting:overview")
    return redirect("access:redeem")


def _database_is_reachable() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        logger.exception("Health-Check: Datenbank nicht erreichbar")
        return False
    return True


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    """Für Docker-Healthcheck und CI: 200 nur, wenn auch die Datenbank antwortet."""
    if _database_is_reachable():
        return JsonResponse({"status": "ok", "database": "ok"})
    return JsonResponse({"status": "error", "database": "unreachable"}, status=503)
