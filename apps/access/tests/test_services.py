from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone
from pytest_django.fixtures import Settings

from apps.access.codes import format_code
from apps.access.models import AccessCode, AccessCodeStatus, FailedAttempt, Participant
from apps.access.services import (
    IssuedCode,
    RedeemError,
    active_participant,
    create_codes,
    redeem_code,
)

pytestmark = pytest.mark.django_db

CLIENT = "203.0.113.7"


def _all_stored_text() -> str:
    """Alle Spalten aller Zugangs-Tabellen als Text, um Klartext-Codes auszuschließen."""
    with connection.cursor() as cursor:
        rows = []
        for table in ("access_accesscode", "access_participant", "access_failedattempt"):
            cursor.execute(f"SELECT * FROM {table}")  # noqa: S608 - feste Tabellennamen
            rows.extend(cursor.fetchall())
    return repr(rows)


def test_codes_are_stored_only_as_hash() -> None:
    issued = create_codes(20, batch="Test")

    stored = _all_stored_text()

    assert AccessCode.objects.count() == 20
    for item in issued:
        assert item.code not in stored
        assert format_code(item.code) not in stored


def test_first_redeem_creates_participant_and_marks_code(issued: IssuedCode) -> None:
    result = redeem_code(format_code(issued.code).lower(), client=CLIENT)

    assert result.error is None
    assert result.participant is not None
    code = AccessCode.objects.get()
    assert code.status == AccessCodeStatus.REDEEMED
    assert code.redeemed_at is not None


def test_redeemed_code_logs_into_same_participant(issued: IssuedCode) -> None:
    first = redeem_code(issued.code, client=CLIENT).participant

    second = redeem_code(issued.code, client="198.51.100.1").participant

    assert first == second
    assert Participant.objects.count() == 1


@pytest.mark.parametrize(
    ("raw", "error"),
    [("ABCD", RedeemError.INVALID_FORMAT), ("ABCD-EFGH-JKMN-PQRS", RedeemError.UNKNOWN)],
)
def test_failed_redeem_is_counted(raw: str, error: RedeemError) -> None:
    result = redeem_code(raw, client=CLIENT)

    assert result.error is error
    assert result.participant is None
    assert FailedAttempt.objects.count() == 1


def test_blocked_code_is_rejected(issued: IssuedCode) -> None:
    AccessCode.objects.update(status=AccessCodeStatus.BLOCKED)

    assert redeem_code(issued.code, client=CLIENT).error is RedeemError.BLOCKED


def test_client_ip_is_not_stored_in_plain_text() -> None:
    redeem_code("ABCD-EFGH-JKMN-PQRS", client=CLIENT)

    assert CLIENT not in _all_stored_text()


def _fail_times(count: int, client: str = CLIENT) -> None:
    for _ in range(count):
        redeem_code("ABCD-EFGH-JKMN-PQRS", client=client)


def test_lockout_after_max_failed_attempts_even_for_valid_code(
    issued: IssuedCode, settings: Settings
) -> None:
    settings.ACCESS_MAX_FAILED_ATTEMPTS = 3
    _fail_times(3)

    result = redeem_code(issued.code, client=CLIENT)

    assert result.error is RedeemError.LOCKED_OUT
    assert not Participant.objects.exists()


def test_lockout_does_not_count_further_attempts(settings: Settings) -> None:
    settings.ACCESS_MAX_FAILED_ATTEMPTS = 3
    _fail_times(10)

    assert FailedAttempt.objects.count() == 3


def test_lockout_is_per_client(issued: IssuedCode, settings: Settings) -> None:
    settings.ACCESS_MAX_FAILED_ATTEMPTS = 3
    _fail_times(3)

    assert redeem_code(issued.code, client="198.51.100.1").participant is not None


def test_lockout_ends_after_window(issued: IssuedCode, settings: Settings) -> None:
    settings.ACCESS_MAX_FAILED_ATTEMPTS = 3
    _fail_times(3)
    FailedAttempt.objects.update(created_at=timezone.now() - timedelta(minutes=61))

    assert redeem_code(issued.code, client=CLIENT).participant is not None


def test_activity_is_written_at_most_once_per_day(issued: IssuedCode) -> None:
    participant = redeem_code(issued.code, client=CLIENT).participant
    assert participant is not None
    yesterday = timezone.now() - timedelta(days=1)
    Participant.objects.update(last_active_at=yesterday)

    active_participant(participant.pk)
    touched = Participant.objects.get().last_active_at
    active_participant(participant.pk)

    assert touched > yesterday
    assert Participant.objects.get().last_active_at == touched


def test_participant_of_blocked_code_is_not_active(issued: IssuedCode) -> None:
    participant = redeem_code(issued.code, client=CLIENT).participant
    assert participant is not None
    AccessCode.objects.update(status=AccessCodeStatus.BLOCKED)

    assert active_participant(participant.pk) is None
