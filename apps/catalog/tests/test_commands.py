from collections.abc import Callable
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from pytest_django.fixtures import Settings

from apps.catalog.models import Facility

pytestmark = pytest.mark.django_db


def test_import_catalog_reports_counts() -> None:
    out = StringIO()

    call_command("import_catalog", str(settings.DEMO_DATA_DIR), stdout=out)

    assert "facilities.csv: 8 neu" in out.getvalue()
    assert Facility.objects.count() == 8


def test_import_catalog_fails_with_exit_code_on_errors(
    replace_in: Callable[[str, str, str], Path],
) -> None:
    directory = replace_in("measures.csv", "M-004,E-003", "M-004,E-999")
    err = StringIO()

    with pytest.raises(CommandError):
        call_command("import_catalog", str(directory), stdout=StringIO(), stderr=err)

    assert "measures.csv, Zeile 5" in err.getvalue()


def test_import_catalog_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(CommandError):
        call_command("import_catalog", str(tmp_path / "fehlt"))


def test_load_demo_data_does_nothing_outside_demo_mode(settings: Settings) -> None:
    settings.DEMO_MODE = False

    call_command("load_demo_data", stdout=StringIO())

    assert not Facility.objects.exists()


def test_load_demo_data_fills_empty_catalog_once(settings: Settings) -> None:
    settings.DEMO_MODE = True
    call_command("load_demo_data", stdout=StringIO())
    Facility.objects.filter(external_id="E-001").update(name="Geändert in der Demo")

    call_command("load_demo_data", stdout=StringIO())

    assert Facility.objects.count() == 8
    assert Facility.objects.get(external_id="E-001").name == "Geändert in der Demo"
