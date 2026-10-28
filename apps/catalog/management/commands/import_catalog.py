"""Importiert den Katalog aus einem Verzeichnis (facilities.csv, measures.csv, expenditures.csv)."""

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.catalog.services import ImportReport, import_catalog


class Command(BaseCommand):
    help = "Importiert Einrichtungen, Maßnahmen und Ausgaben aus CSV-Dateien (wiederholbar)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("directory", type=Path, help="Verzeichnis mit den drei CSV-Dateien")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Nur prüfen und Vorschau zeigen, nichts speichern.",
        )

    def handle(self, *args: Any, directory: Path, dry_run: bool, **options: Any) -> None:
        if not directory.is_dir():
            raise CommandError(f"Verzeichnis nicht gefunden: {directory}")
        report = import_catalog(directory, dry_run=dry_run)
        write_report(self, report)


def write_report(command: BaseCommand, report: ImportReport) -> None:
    for summary in report.files:
        command.stdout.write(
            f"{summary.file}: {summary.new} neu, {summary.updated} geändert, "
            f"{summary.skipped} unverändert"
        )
    if not report.ok:
        for error in report.errors:
            command.stderr.write(str(error))
        raise CommandError(f"Import abgebrochen, nichts gespeichert ({len(report.errors)} Fehler).")
    if report.dry_run:
        command.stdout.write("Probelauf: nichts gespeichert.")
    else:
        command.stdout.write(command.style.SUCCESS("Import gespeichert."))
