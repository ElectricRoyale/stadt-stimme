"""Ergebnisse als CSV für Verwaltung und Gemeinderat.

Semikolon und Dezimalkomma, mit BOM, damit deutsche Tabellenprogramme die Datei direkt in Spalten
öffnen. Texte aus dem Katalog werden gegen Formel-Injektion geschützt (``=``, ``+``, ``-``, ``@``
am Anfang wird ein Apostroph vorangestellt).
"""

import csv
import io
from collections.abc import Iterable
from decimal import Decimal

from apps.reporting.results import GapRow, Results

HEADER = [
    "Art",
    "Name",
    "Thema",
    "Adresse",
    "Anteil Bürgerpunkte (%)",
    "Anteil Ausgaben (%)",
    "Lücke (Prozentpunkte)",
    "Punkte",
    "Ausgaben (€)",
]
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def safe_text(value: str) -> str:
    return f"'{value}" if value.startswith(_FORMULA_START) else value


def _amount(value: Decimal) -> str:
    return f"{value:.2f}".replace(".", ",")


def _row(row: GapRow) -> list[str]:
    return [
        "Ganzes Thema" if row.is_theme else "Einrichtung",
        safe_text(row.name),
        safe_text(row.category.name),
        safe_text(row.facility.address if row.facility else ""),
        str(row.wish),
        str(row.spend),
        str(row.gap),
        str(row.points),
        _amount(row.spend_amount),
    ]


def results_csv(results: Results, city: str) -> str:
    """Alle Einrichtungen, dann alle ganzen Themen, jeweils nach Lücke absteigend."""
    buffer = io.StringIO()
    year = f"Ist-Ausgaben {results.fiscal_year}" if results.fiscal_year else "Keine Ist-Ausgaben"
    buffer.write(f"# StadtStimme {safe_text(city)}, Ergebnisse. {year}.\r\n")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(HEADER)
    rows: Iterable[GapRow] = [*results.places, *results.themes]
    writer.writerows(_row(r) for r in rows)
    return "﻿" + buffer.getvalue()
