from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.catalog.models import (
    Building,
    Category,
    Expenditure,
    ExpenditureKind,
    Facility,
    Measure,
    MeasureStatus,
)


@pytest.fixture
def pool() -> Facility:
    sport = Category.objects.create(name="Sport")
    return Facility.objects.create(external_id="E-1", name="Hallenbad", category=sport)


@pytest.fixture
def library() -> Facility:
    culture = Category.objects.create(name="Kultur")
    return Facility.objects.create(external_id="E-2", name="Bibliothek", category=culture)


def _expenditure(facility: Facility, **overrides: object) -> Expenditure:
    values: dict[str, object] = {
        "facility": facility,
        "fiscal_year": 2025,
        "amount": Decimal("1000.00"),
        "kind": ExpenditureKind.ACTUAL,
        "source": "Haushalt",
        "as_of": date(2026, 3, 31),
    }
    values.update(overrides)
    return Expenditure(**values)


@pytest.mark.django_db
def test_new_measure_is_open(pool: Facility) -> None:
    measure = Measure.objects.create(external_id="M-1", facility=pool, title="Dach")

    assert measure.status == MeasureStatus.OPEN


@pytest.mark.django_db
def test_expenditure_rejects_measure_of_other_facility(pool: Facility, library: Facility) -> None:
    roof = Measure.objects.create(external_id="M-1", facility=pool, title="Dach")

    with pytest.raises(ValidationError) as error:
        _expenditure(library, measure=roof).full_clean()

    assert "measure" in error.value.message_dict


@pytest.mark.django_db
def test_expenditure_without_measure_is_unique_per_year_and_kind(pool: Facility) -> None:
    _expenditure(pool).save()

    with pytest.raises(IntegrityError):
        _expenditure(pool, amount=Decimal("5.00")).save()


@pytest.mark.django_db
def test_plan_and_actual_may_coexist(pool: Facility) -> None:
    _expenditure(pool).save()
    _expenditure(pool, kind=ExpenditureKind.PLAN).save()

    assert Expenditure.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides",
    [{"amount": Decimal("-1.00")}, {"fiscal_year": 1999}, {"fiscal_year": 2101}],
)
def test_expenditure_rejects_implausible_values(
    pool: Facility, overrides: dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        _expenditure(pool, **overrides).full_clean()


@pytest.mark.django_db
def test_measure_rejects_building_of_other_facility(pool: Facility, library: Facility) -> None:
    reading_room = Building.objects.create(external_id="G-1", facility=library, name="Lesesaal")
    measure = Measure(external_id="M-1", facility=pool, building=reading_room, title="Dach")

    with pytest.raises(ValidationError) as error:
        measure.full_clean()

    assert "building" in error.value.message_dict


@pytest.mark.django_db
def test_measure_accepts_building_of_own_facility(pool: Facility) -> None:
    hall = Building.objects.create(external_id="G-1", facility=pool, name="Schwimmhalle")

    Measure(external_id="M-1", facility=pool, building=hall, title="Dach").full_clean()
