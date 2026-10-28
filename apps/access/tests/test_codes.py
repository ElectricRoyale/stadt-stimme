import pytest
from pytest_django.fixtures import Settings

from apps.access.codes import (
    ALPHABET,
    CODE_LENGTH,
    format_code,
    generate_code,
    hash_code,
    normalize_code,
)


def test_generated_code_has_16_crockford_characters() -> None:
    code = generate_code()

    assert len(code) == CODE_LENGTH
    assert set(code) <= set(ALPHABET)


def test_generated_codes_differ() -> None:
    assert len({generate_code() for _ in range(1000)}) == 1000


@pytest.mark.parametrize(
    "raw",
    ["ABCD-EFGH-JKMN-PQRS", "abcd efgh jkmn pqrs", " ABCDEFGHJKMNPQRS ", "abcd-efgh-jkmn-pqrs"],
)
def test_normalize_accepts_common_spellings(raw: str) -> None:
    assert normalize_code(raw) == "ABCDEFGHJKMNPQRS"


def test_normalize_maps_confusable_letters() -> None:
    assert normalize_code("OOOO-IIII-LLLL-oil0") == "0000111111110110"


@pytest.mark.parametrize(
    "raw", ["", "ABCD-EFGH-JKMN", "ABCD-EFGH-JKMN-PQRS-T", "ABCD-EFGH-JKMN-PQRU"]
)
def test_normalize_rejects_wrong_length_or_characters(raw: str) -> None:
    assert normalize_code(raw) is None


def test_format_groups_by_four() -> None:
    assert format_code("ABCDEFGHJKMNPQRS") == "ABCD-EFGH-JKMN-PQRS"


def test_hash_is_stable_and_depends_on_pepper(settings: Settings) -> None:
    settings.ACCESS_CODE_PEPPER = "eins"
    first = hash_code("ABCDEFGHJKMNPQRS")
    assert hash_code("ABCDEFGHJKMNPQRS") == first

    settings.ACCESS_CODE_PEPPER = "zwei"
    assert hash_code("ABCDEFGHJKMNPQRS") != first
    assert "ABCDEFGHJKMNPQRS" not in first
