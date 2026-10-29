from collections.abc import Callable
from pathlib import Path

import pytest
from django.conf import settings

from apps.catalog.models import (
    Building,
    Category,
    Expenditure,
    Facility,
    Measure,
    MeasureStatus,
)
from apps.catalog.services import import_catalog

pytestmark = pytest.mark.django_db

Replace = Callable[[str, str, str], Path]


def _counts() -> tuple[int, int, int, int, int]:
    return (
        Category.objects.count(),
        Facility.objects.count(),
        Building.objects.count(),
        Measure.objects.count(),
        Expenditure.objects.count(),
    )


def test_demo_data_imports_completely() -> None:
    report = import_catalog(settings.DEMO_DATA_DIR)

    assert report.ok, report.errors
    assert _counts() == (5, 8, 5, 12, 9)
    assert Measure.objects.get(external_id="M-005").status == MeasureStatus.IN_PROGRESS
    assert Expenditure.objects.filter(measure__external_id="M-005").count() == 1
    assert Measure.objects.get(external_id="M-005").building == Building.objects.get(
        external_id="G-003"
    )
    assert Measure.objects.get(external_id="M-002").building is None


def test_reimport_is_idempotent() -> None:
    import_catalog(settings.DEMO_DATA_DIR)

    report = import_catalog(settings.DEMO_DATA_DIR)

    assert report.ok
    assert _counts() == (5, 8, 5, 12, 9)
    assert all(summary.new == 0 and summary.updated == 0 for summary in report.files)


def test_reimport_updates_changed_rows(replace_in: Replace) -> None:
    import_catalog(settings.DEMO_DATA_DIR)
    directory = replace_in("facilities.csv", "Stadtbibliothek", "Stadtbücherei")

    report = import_catalog(directory)

    assert report.ok
    assert Facility.objects.get(external_id="E-004").name == "Stadtbücherei"
    assert report.files[0].updated == 1


def test_dry_run_saves_nothing() -> None:
    report = import_catalog(settings.DEMO_DATA_DIR, dry_run=True)

    assert report.ok
    assert report.files[-1].new == 9
    assert _counts() == (0, 0, 0, 0, 0)


@pytest.mark.parametrize(
    ("filename", "old", "new", "expected"),
    [
        ("measures.csv", "M-004,E-003", "M-004,E-999", "'E-999' nicht gefunden"),
        ("measures.csv", "Pausenhof.,offen", "Pausenhof.,erledigt", "Unbekannter Wert 'erledigt'"),
        ("expenditures.csv", "E-003,M-005", "E-001,M-005", "anderen Einrichtung"),
        ("expenditures.csv", "E-007,,2025,74000.00", "E-007,,2025,-1", "nicht negativ"),
        ("expenditures.csv", "Ist,", "Soll,", "Erlaubt: Plan, Ist"),
    ],
)
def test_invalid_row_aborts_whole_import(
    replace_in: Replace, filename: str, old: str, new: str, expected: str
) -> None:
    report = import_catalog(replace_in(filename, old, new))

    assert not report.ok
    assert any(error.file == filename and expected in error.message for error in report.errors)
    assert _counts() == (0, 0, 0, 0, 0)


def test_error_names_the_line_as_shown_in_an_editor(replace_in: Replace) -> None:
    report = import_catalog(replace_in("measures.csv", "M-004,E-003", "M-004,E-999"))

    assert [error.row for error in report.errors] == [5]


def test_missing_file_is_reported(demo_copy: Path) -> None:
    (demo_copy / "expenditures.csv").unlink()

    report = import_catalog(demo_copy)

    assert [error.file for error in report.errors] == ["expenditures.csv"]
    assert _counts() == (0, 0, 0, 0, 0)


def test_row_with_too_many_columns_is_reported(demo_copy: Path) -> None:
    path = demo_copy / "facilities.csv"
    extra_row = "E-999,Bad,Sport,Weg 1,Text,50.1,9.1,überzählig\n"
    path.write_text(path.read_text(encoding="utf-8") + extra_row, encoding="utf-8")

    report = import_catalog(demo_copy)

    assert [error.file for error in report.errors] == ["facilities.csv"]
    assert "mehr Spalten" in report.errors[0].message
    assert _counts() == (0, 0, 0, 0, 0)


def test_excel_byte_order_mark_is_accepted(demo_copy: Path) -> None:
    path = demo_copy / "facilities.csv"
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())

    report = import_catalog(demo_copy)

    assert report.ok, report.errors


def test_measure_with_building_of_other_facility_is_rejected(replace_in: Replace) -> None:
    directory = replace_in("measures.csv", "M-001,E-001,G-001", "M-001,E-001,G-003")

    report = import_catalog(directory)

    assert [(error.file, error.row) for error in report.errors] == [("measures.csv", 2)]
    assert "anderen Einrichtung" in report.errors[0].message
    assert _counts() == (0, 0, 0, 0, 0)


def test_unknown_building_is_reported(replace_in: Replace) -> None:
    directory = replace_in("measures.csv", "M-001,E-001,G-001", "M-001,E-001,G-999")

    report = import_catalog(directory)

    assert [error.file for error in report.errors] == ["measures.csv"]
    assert "nicht gefunden" in report.errors[0].message


def test_coordinates_are_imported() -> None:
    import_catalog(settings.DEMO_DATA_DIR)

    facility = Facility.objects.get(external_id="E-001")
    assert facility.has_location
    assert str(facility.latitude) == "49.484000"


def test_coordinates_are_optional(demo_copy: Path) -> None:
    path = demo_copy / "facilities.csv"
    rows = [line.rsplit(",", 2)[0] for line in path.read_text(encoding="utf-8").splitlines()]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    report = import_catalog(demo_copy)

    assert report.ok, report.errors
    assert not Facility.objects.get(external_id="E-001").has_location


def test_latitude_without_longitude_is_reported(replace_in: Replace) -> None:
    directory = replace_in("facilities.csv", ",49.484000,8.492000", ",49.484000,")

    report = import_catalog(directory)

    assert [error.file for error in report.errors] == ["facilities.csv"]
    assert "zusammen" in report.errors[0].message
