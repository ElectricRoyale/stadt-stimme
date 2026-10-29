"""Kartendaten für Übersicht und Ergebnisse, als JSON für ``json_script`` (nur Werte, kein HTML)."""

from typing import Any

from apps.catalog.models import Facility, Measure
from apps.points.overview import sentence_case
from apps.reporting.results import Results
from apps.reporting.statistics import Overview, PlaceStat


def map_payload(overview: Overview, results: Results) -> dict[str, Any]:
    """Alle Einrichtungen für Karte und Liste; ohne Koordinaten nur in der Liste (lat/lng None)."""
    spend = {r.key: r.spend for r in results.places}
    return {
        "places": [
            _place(p, p.facility, spend.get(p.target.key, 0))
            for p in overview.places
            if p.facility is not None
        ]
    }


def _place(place: PlaceStat, facility: Facility, spend: int) -> dict[str, Any]:
    located = facility.has_location
    return {
        "key": place.target.key,
        "name": place.name,
        "address": facility.address,
        "theme": place.category.pk,
        "themeName": place.category.name,
        "color": place.category.color,
        "lat": float(facility.latitude or 0) if located else None,
        "lng": float(facility.longitude or 0) if located else None,
        "share": place.share,
        "spend": spend,
        "mine": place.mine,
        "measures": [_measure(m) for m in facility.measures.all()],
    }


def _measure(measure: Measure) -> dict[str, str]:
    return {
        "title": measure.title,
        "status": sentence_case(measure.get_status_display()),
        "statusKey": measure.status,
    }


def results_payload(results: Results) -> dict[str, Any]:
    """Marker der Ergebniskarte: nur Einrichtungen mit Koordinaten, Lücke als Größe und Farbe."""
    return {
        "places": [
            {
                "key": row.key,
                "name": row.name,
                "theme": row.category.pk,
                "gap": row.gap,
                "gapText": row.gap_text,
                "tone": row.tone,
                "lat": float(row.facility.latitude or 0),
                "lng": float(row.facility.longitude or 0),
            }
            for row in results.places
            if row.facility is not None and row.facility.has_location
        ],
        "scale": results.gap_scale,
    }
