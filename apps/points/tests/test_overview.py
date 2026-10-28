from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import Expenditure, ExpenditureKind, Measure, MeasureStatus
from apps.points.overview import Spending, build_groups, format_eur
from apps.points.services import Target
from apps.points.tests.conftest import Catalog

THIS_YEAR = timezone.localdate().year


@pytest.mark.parametrize(
    ("amount", "text"),
    [
        (Decimal("612000"), "612.000 €"),
        (Decimal("1480000"), "1,5 Mio. €"),
        (Decimal("0"), "0 €"),
    ],
)
def test_format_eur(amount: Decimal, text: str) -> None:
    assert format_eur(amount) == text


def _expense(catalog: Catalog, year: int, amount: str, kind: str) -> Expenditure:
    return Expenditure.objects.create(
        facility=catalog.bad,
        fiscal_year=year,
        amount=Decimal(amount),
        kind=kind,
        source="Test",
        as_of=date(THIS_YEAR, 1, 1),
    )


@pytest.mark.django_db
def test_spending_sums_recent_actuals_and_next_plan(catalog: Catalog) -> None:
    items = [
        _expense(catalog, THIS_YEAR - 1, "100000", ExpenditureKind.ACTUAL),
        _expense(catalog, THIS_YEAR - 2, "200000", ExpenditureKind.ACTUAL),
        _expense(catalog, THIS_YEAR - 9, "999999", ExpenditureKind.ACTUAL),
        _expense(catalog, THIS_YEAR, "50000", ExpenditureKind.PLAN),
        _expense(catalog, THIS_YEAR + 1, "70000", ExpenditureKind.PLAN),
    ]

    spending = Spending.of(items)

    assert spending.actual_text == "300.000 €"
    assert spending.actual_label == f"Ausgaben {THIS_YEAR - 2}\u2013{THIS_YEAR - 1}"
    assert spending.planned_text == "50.000 €"
    assert spending.planned_label == f"Geplant {THIS_YEAR}"


def test_spending_without_data() -> None:
    spending = Spending.of([])

    assert spending.actual_text == "keine Angaben"
    assert spending.planned_text == "keine Angaben"


@pytest.mark.django_db
def test_build_groups_puts_general_row_first(catalog: Catalog) -> None:
    Measure.objects.create(
        external_id="M-1", facility=catalog.bad, title="Dach", status=MeasureStatus.DECIDED
    )

    groups = build_groups({Target("f", catalog.bad.pk): 12})

    assert [g.category.name for g in groups] == ["Bildung", "Sport"]
    sport = groups[1]
    assert [r.name for r in sport.rows] == ["Sport allgemein", "Hallenbad", "Sporthalle"]
    assert sport.points == 12
    bad = sport.rows[1]
    assert [(e.title, e.status, e.tone) for e in bad.entries] == [("Dach", "Beschlossen", "plan")]


@pytest.mark.django_db
def test_categories_get_distinct_colors(catalog: Catalog) -> None:
    assert catalog.sport.color != catalog.bildung.color
    assert catalog.sport.color
