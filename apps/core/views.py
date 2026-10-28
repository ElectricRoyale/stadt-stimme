"""Querschnittliche Seiten: Startseite und Health-Check."""

import logging

from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "core/home.html")


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
