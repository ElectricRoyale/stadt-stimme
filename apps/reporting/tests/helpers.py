from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.access.models import Participant
from apps.access.services import create_codes, redeem_code
from apps.catalog.models import Expenditure, ExpenditureKind, Facility

LAST_YEAR = timezone.localdate().year - 1


def new_person() -> Participant:
    result = redeem_code(create_codes(1, batch="T")[0].code, client="10.0.0.1")
    if result.participant is None:
        raise AssertionError(result.error)
    return result.participant


def spend(facility: Facility, amount: str, year: int = LAST_YEAR) -> None:
    Expenditure.objects.create(
        facility=facility,
        fiscal_year=year,
        amount=Decimal(amount),
        kind=ExpenditureKind.ACTUAL,
        source="Test",
        as_of=date(year + 1, 1, 31),
    )
