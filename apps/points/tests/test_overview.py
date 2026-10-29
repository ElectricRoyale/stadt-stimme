from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import Expenditure, ExpenditureKind, Facility, Measure, MeasureStatus
from apps.points.overview import (
    build_groups,
    format_eur,
    format_share,
    lead_group,
    ledger_cells,
)
from apps.points.services import Target
from apps.points.tests.conftest import Catalog

LAST_YEAR = timezone.localdate().year - 1


@pytest.mark.parametrize(
    ("amount", "text"),
    [(Decimal("612000"), "612.000 €"), (Decimal("1480000"), "1.480.000 €"), (Decimal(0), "0 €")],
)
def test_format_eur(amount: Decimal, text: str) -> None:
    assert format_eur(amount) == text


def test_format_share() -> None:
    assert format_share(37.84) == "37,8"


def _actual(facility: Facility, amount: str, year: int = LAST_YEAR) -> None:
    Expenditure.objects.create(
        facility=facility,
        fiscal_year=year,
        amount=Decimal(amount),
        kind=ExpenditureKind.ACTUAL,
        source="Test",
        as_of=date(year, 12, 31),
    )


@pytest.mark.django_db
def test_build_groups_puts_general_row_first(catalog: Catalog) -> None:
    Measure.objects.create(
        external_id="M-1", facility=catalog.bad, title="Dach", status=MeasureStatus.DECIDED
    )

    groups = build_groups({Target("f", catalog.bad.pk): 12}, None)

    assert [g.category.name for g in groups] == ["Bildung", "Sport"]
    sport = groups[1]
    assert [r.name for r in sport.rows] == ["Sport allgemein", "Hallenbad", "Sporthalle"]
    assert sport.points == 12
    assert [m.title for m in sport.rows[1].measures] == ["Dach"]
    assert sport.rows[1].spend_text == "keine Angaben"


@pytest.mark.django_db
def test_spending_shares_use_only_the_given_year(catalog: Catalog) -> None:
    _actual(catalog.bad, "600000")
    _actual(catalog.schule, "200000")
    _actual(catalog.halle, "999999", year=LAST_YEAR - 1)

    groups = build_groups({}, LAST_YEAR)

    bildung, sport = groups
    assert bildung.spend_share == 25
    assert sport.spend_share == 75
    assert sport.rows[1].spend_text == "600.000 € (75,0 %)"
    assert sport.rows[2].spend is None


@pytest.mark.django_db
def test_ledger_cells_places_before_general_then_free(catalog: Catalog) -> None:
    groups = build_groups({Target("c", catalog.sport.pk): 2, Target("f", catalog.bad.pk): 3}, None)

    cells = ledger_cells(groups, 10)

    keys = [(c.key, c.general) for c in cells]
    bad, sport = f"f-{catalog.bad.pk}", f"c-{catalog.sport.pk}"
    assert keys == [(bad, False)] * 3 + [(sport, True)] * 2 + [(None, False)] * 5


@pytest.mark.django_db
def test_lead_group_is_theme_most_above_its_spending(catalog: Catalog) -> None:
    _actual(catalog.bad, "900000")
    _actual(catalog.schule, "100000")
    groups = build_groups(
        {Target("f", catalog.schule.pk): 40, Target("f", catalog.bad.pk): 60}, LAST_YEAR
    )

    lead = lead_group(groups)

    assert lead is not None
    assert lead.category == catalog.bildung  # 40 Punkte gegen 10 % Ausgaben
    assert lead_group(build_groups({}, LAST_YEAR)) is None
