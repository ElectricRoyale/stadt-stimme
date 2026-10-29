"""Kartendaten für Übersicht und Ergebnisse, als JSON für ``json_script`` (nur Werte, kein HTML)."""

from typing import Any

from apps.catalog.models import Facility, Measure
from apps.points.overview import sentence_case
from apps.reporting.results import GapRow, Results
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


def results_payload(results: Results, give_url: str) -> dict[str, Any]:
    """Alle Zeilen für die Detailansicht; Marker nur für Einrichtungen mit Koordinaten."""
    return {
        "rows": [_gap_row(r, give_url) for r in results.rows],
        "scaleMax": results.scale_max,
    }


def _gap_row(row: GapRow, give_url: str) -> dict[str, Any]:
    facility = row.facility
    located = facility is not None and facility.has_location
    return {
        "key": row.key,
        "name": row.name,
        "kicker": row.kicker,
        "color": row.category.color,
        "isTheme": row.is_theme,
        "wish": row.wish,
        "spend": row.spend,
        "gapText": row.gap_text,
        "tone": row.tone,
        "summary": row.summary,
        "mine": row.mine,
        "give": f"{give_url}#id_{row.key}",
        "lat": float(facility.latitude or 0) if located and facility else None,
        "lng": float(facility.longitude or 0) if located and facility else None,
    }
