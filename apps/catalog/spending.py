"""Ist-Ausgaben des letzten abgeschlossenen Haushaltsjahres (ADR-006).

Gemeinsame Grundlage für „Punkte verteilen“, Übersicht und Ergebnisse, damit alle Seiten
dasselbe Jahr und dieselben Summen zeigen.
"""

from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.catalog.models import Expenditure, ExpenditureKind


def last_closed_fiscal_year() -> int | None:
    """Jüngstes Jahr vor dem laufenden, für das Ist-Ausgaben eingetragen sind."""
    year: int | None = (
        Expenditure.objects.filter(
            kind=ExpenditureKind.ACTUAL, fiscal_year__lt=timezone.localdate().year
        )
        .order_by("-fiscal_year")
        .values_list("fiscal_year", flat=True)
        .first()
    )
    return year


def actual_spend_by_facility(fiscal_year: int | None) -> dict[int, Decimal]:
    """Ist-Ausgaben je Einrichtung; leer ohne abgeschlossenes Haushaltsjahr."""
    if fiscal_year is None:
        return {}
    rows = (
        Expenditure.objects.filter(kind=ExpenditureKind.ACTUAL, fiscal_year=fiscal_year)
        .values("facility_id")
        .annotate(total=Sum("amount"))
    )
    return {row["facility_id"]: row["total"] for row in rows}
