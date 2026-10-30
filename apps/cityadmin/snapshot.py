"""Stichtags-Export (M7): Punkte und Unterstützer je Ziel zum Ende eines Tages, aus dem Log."""

import csv
import io
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from apps.catalog.models import Category, Facility
from apps.points.snapshot import Tally, tally_at
from apps.points.targets import Target
from apps.reporting.export import safe_text

HEADER = ["Art", "Name", "Thema", "Punkte", "Unterstützer"]


def end_of_day(day: date) -> datetime:
    """Letzter Moment des Tages in der Zeitzone der Stadt."""
    start = timezone.make_aware(datetime.combine(day + timedelta(days=1), time.min))
    return start - timedelta(microseconds=1)


def snapshot_csv(day: date, city: str) -> str:
    """Einrichtungen, dann ganze Themen, jeweils nach Punkten absteigend. Semikolon, BOM."""
    tallies = tally_at(end_of_day(day))
    facilities = Facility.objects.select_related("category").in_bulk(
        [t.pk for t in tallies if t.kind == "f"]
    )
    categories = Category.objects.in_bulk([t.pk for t in tallies if t.kind == "c"])

    def row(target: Target, tally: Tally) -> list[str]:
        if target.kind == "f":
            facility = facilities[target.pk]
            return ["Einrichtung", facility.name, facility.category.name]
        category = categories[target.pk]
        return ["Ganzes Thema", f"{category.name} allgemein", category.name]

    ordered = sorted(
        tallies.items(), key=lambda item: (item[0].kind != "f", -item[1].points, item[0].pk)
    )
    buffer = io.StringIO()
    buffer.write(f"# StadtStimme {safe_text(city)}, Stichtag {day:%d.%m.%Y}, Tagesende.\r\n")
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(HEADER)
    for target, tally in ordered:
        writer.writerow(
            [*(safe_text(v) for v in row(target, tally)), str(tally.points), str(tally.supporters)]
        )
    return "﻿" + buffer.getvalue()
