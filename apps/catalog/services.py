"""Import des Katalogs aus einem Verzeichnis mit vier CSV-Dateien.

Die Dateien hängen voneinander ab (Gebäude und Maßnahmen verweisen auf Einrichtungen, Ausgaben
auf Einrichtungen und Maßnahmen). Deshalb laufen alle in einer Transaktion: Bei einem einzigen
Fehler oder im Probelauf wird alles zurückgerollt.
"""

from dataclasses import dataclass, field
from pathlib import Path

import tablib
from django.core.exceptions import ValidationError
from django.db import transaction
from import_export.resources import ModelResource
from import_export.results import Result
from tablib.exceptions import InvalidDimensions

from apps.catalog.models import Facility
from apps.catalog.resources import (
    BuildingResource,
    ExpenditureResource,
    FacilityResource,
    MeasureResource,
)

CATALOG_FILES: tuple[tuple[str, type[ModelResource]], ...] = (
    ("facilities.csv", FacilityResource),
    ("buildings.csv", BuildingResource),
    ("measures.csv", MeasureResource),
    ("expenditures.csv", ExpenditureResource),
)


@dataclass(frozen=True)
class RowError:
    file: str
    row: int | None
    message: str

    def __str__(self) -> str:
        where = f"{self.file}, Zeile {self.row}" if self.row else self.file
        return f"{where}: {self.message}"


@dataclass(frozen=True)
class FileSummary:
    file: str
    new: int
    updated: int
    skipped: int


@dataclass
class ImportReport:
    dry_run: bool
    files: list[FileSummary] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def committed(self) -> bool:
        return self.ok and not self.dry_run


def catalog_is_empty() -> bool:
    return not Facility.objects.exists()


def import_catalog(directory: Path, *, dry_run: bool = False) -> ImportReport:
    """Importiert die Dateien aus ``CATALOG_FILES`` in dieser Reihenfolge aus ``directory``."""
    report = ImportReport(dry_run=dry_run)
    with transaction.atomic():
        for filename, resource_class in CATALOG_FILES:
            _import_file(directory / filename, resource_class, report)
            if not report.ok:
                break
        if not report.committed:
            transaction.set_rollback(True)
    return report


def _import_file(path: Path, resource_class: type[ModelResource], report: ImportReport) -> None:
    try:
        dataset = _load_csv(path)
    except InvalidDimensions:
        report.errors.append(
            RowError(path.name, None, "Eine Zeile hat mehr Spalten als die Kopfzeile.")
        )
        return
    except (OSError, ValueError) as error:
        report.errors.append(RowError(path.name, None, f"Datei nicht lesbar: {error}"))
        return

    result = resource_class().import_data(dataset, dry_run=False, use_transactions=False)
    report.errors.extend(_collect_errors(path.name, result))
    totals = result.totals
    report.files.append(
        FileSummary(
            file=path.name,
            new=totals["new"],
            updated=totals["update"],
            skipped=totals["skip"],
        )
    )


def _load_csv(path: Path) -> tablib.Dataset:
    # utf-8-sig entfernt das BOM, das Excel beim CSV-Export voranstellt.
    text = path.read_text(encoding="utf-8-sig")
    return tablib.Dataset().load(text, format="csv")


def _collect_errors(filename: str, result: Result) -> list[RowError]:
    errors = [RowError(filename, None, str(error.error)) for error in result.base_errors]
    for invalid in result.invalid_rows:
        errors.append(RowError(filename, _csv_line(invalid.number), _format(invalid.error)))
    for number, row_errors in result.row_errors():
        for error in row_errors:
            errors.append(RowError(filename, _csv_line(number), str(error.error)))
    return errors


def _csv_line(row_number: int) -> int:
    """Zeilennummer wie im Editor: Datenzeile 1 steht in Zeile 2 (nach der Kopfzeile)."""
    return row_number + 1


def _format(error: ValidationError) -> str:
    if hasattr(error, "error_dict"):
        return " | ".join(
            f"{name}: {' '.join(messages)}" for name, messages in error.message_dict.items()
        )
    return " ".join(error.messages)
