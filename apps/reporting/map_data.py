"""Kartendaten für Übersicht und Ergebnisse, als JSON für ``json_script`` (nur Werte, kein HTML)."""

from typing import Any

from apps.catalog.models import Facility, Measure
from apps.points.overview import STATUS_TONE, sentence_case
from apps.reporting.results import GapRow, Results
from apps.reporting.statistics import Overview, PlaceStat, ThemeStat


def map_payload(overview: Overview) -> dict[str, Any]:
    located = [(p, p.facility) for p in overview.places if p.facility and p.facility.has_location]
    places = [p for p, _ in located]
    return {
        "places": [_place(p, f) for p, f in located],
        "themes": [_theme(t, places) for t in overview.themes],
    }


def _place(place: PlaceStat, facility: Facility) -> dict[str, Any]:
    return {
        "key": place.target.key,
        "name": place.name,
        "theme": place.category.pk,
        "themeName": place.category.name,
        "color": place.category.color,
        "lat": float(facility.latitude or 0),
        "lng": float(facility.longitude or 0),
        "share": place.share,
        "mine": place.mine,
        "measures": [_measure(m) for m in facility.measures.all()],
    }


def _measure(measure: Measure) -> dict[str, str]:
    return {
        "title": measure.title,
        "status": sentence_case(measure.get_status_display()),
        "tone": STATUS_TONE[measure.status],
    }


def _theme(theme: ThemeStat, places: list[PlaceStat]) -> dict[str, Any]:
    """Thema als Blase im Schwerpunkt seiner Einrichtungen (Ebene „Bereiche“)."""
    own = [p.facility for p in places if p.category == theme.category and p.facility]
    return {
        "id": theme.category.pk,
        "key": f"c-{theme.category.pk}",
        "name": theme.category.name,
        "color": theme.category.color,
        "share": theme.citizen_share,
        "generalShare": theme.general_share,
        "mine": theme.mine,
        "lat": _mean([float(f.latitude or 0) for f in own]),
        "lng": _mean([float(f.longitude or 0) for f in own]),
        "places": [p.target.key for p in places if p.category == theme.category],
    }


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


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
