import csv
from collections.abc import Callable
from io import StringIO

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from pytest_django.fixtures import Settings

from apps.access.models import AccessCode
from apps.access.services import redeem_code

pytestmark = pytest.mark.django_db


def test_create_access_codes_prints_redeemable_codes_once() -> None:
    out = StringIO()

    call_command("create_access_codes", "3", "--batch", "Test", stdout=out, stderr=StringIO())

    rows = list(csv.DictReader(StringIO(out.getvalue())))
    assert len(rows) == 3
    assert AccessCode.objects.filter(batch="Test").count() == 3
    assert redeem_code(rows[0]["code"], client="127.0.0.1").participant is not None


@pytest.mark.parametrize("count", ["0", "100001"])
def test_create_access_codes_rejects_bad_count(count: str) -> None:
    with pytest.raises(CommandError):
        call_command("create_access_codes", count, "--batch", "Test")


def test_load_demo_codes_does_nothing_outside_demo_mode(settings: Settings) -> None:
    settings.DEMO_MODE = False

    call_command("load_demo_codes", stdout=StringIO())

    assert not AccessCode.objects.exists()


def test_load_demo_codes_runs_once_and_codes_from_readme_work(
    demo_mode: Callable[[bool], None],
) -> None:
    demo_mode(True)

    call_command("load_demo_codes", stdout=StringIO())
    call_command("load_demo_codes", stdout=StringIO())

    assert AccessCode.objects.count() == 5
    readme = (settings.BASE_DIR / "README.md").read_text(encoding="utf-8")
    assert "3N80-JG4V-WS61-P663" in readme
    assert redeem_code("3N80-JG4V-WS61-P663", client="127.0.0.1").participant is not None
