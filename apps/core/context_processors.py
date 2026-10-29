from django.conf import settings
from django.http import HttpRequest


def city(request: HttpRequest) -> dict[str, str]:
    return {"city_name": settings.CITY_NAME}


def map_tiles(request: HttpRequest) -> dict[str, str]:
    """Kachelserver für alle Karten, samt Ausweichserver (ADR-012)."""
    return {
        "map_tile_url": settings.MAP_TILE_URL,
        "map_attribution": settings.MAP_ATTRIBUTION,
        "map_tile_fallback_url": settings.MAP_TILE_FALLBACK_URL,
        "map_fallback_attribution": settings.MAP_FALLBACK_ATTRIBUTION,
    }
