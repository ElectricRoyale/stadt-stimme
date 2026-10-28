"""Datenpflege für Markus (M2, M3): Formulare und CSV-Import mit Vorschau.

Reihenfolge beim Import über die Oberfläche: Einrichtungen, Gebäude, Maßnahmen, Ausgaben.
Für alle Dateien auf einmal gibt es den Befehl ``import_catalog``.
"""

from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import CSV

from apps.catalog.models import Building, Category, Expenditure, Facility, Measure
from apps.catalog.resources import (
    BuildingResource,
    ExpenditureResource,
    FacilityResource,
    MeasureResource,
)


class _CsvImportExportAdmin(ImportExportModelAdmin):
    formats = [CSV]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "facility_count"]
    search_fields = ["name"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        queryset: QuerySet[Category] = super().get_queryset(request)
        return queryset.annotate(_facility_count=Count("facilities"))

    @admin.display(description="Einrichtungen", ordering="_facility_count")
    def facility_count(self, obj: Category) -> int:
        return int(getattr(obj, "_facility_count", 0))


class BuildingInline(admin.TabularInline):
    model = Building
    fields = ["external_id", "name", "address"]
    extra = 0
    show_change_link = True


class MeasureInline(admin.TabularInline):
    model = Measure
    fields = ["external_id", "title", "building", "status"]
    extra = 0
    show_change_link = True


@admin.register(Facility)
class FacilityAdmin(_CsvImportExportAdmin):
    resource_classes = [FacilityResource]
    list_display = ["name", "category", "address", "external_id"]
    list_filter = ["category"]
    search_fields = ["name", "external_id", "address"]
    list_select_related = ["category"]
    inlines = [BuildingInline, MeasureInline]


@admin.register(Building)
class BuildingAdmin(_CsvImportExportAdmin):
    resource_classes = [BuildingResource]
    list_display = ["name", "facility", "address", "external_id"]
    list_filter = ["facility__category"]
    search_fields = ["name", "external_id", "address", "facility__name"]
    list_select_related = ["facility"]
    autocomplete_fields = ["facility"]


@admin.register(Measure)
class MeasureAdmin(_CsvImportExportAdmin):
    resource_classes = [MeasureResource]
    list_display = ["title", "facility", "building", "status", "external_id"]
    list_filter = ["status", "facility__category"]
    search_fields = ["title", "external_id", "facility__name", "building__name"]
    list_select_related = ["facility", "building"]
    autocomplete_fields = ["facility", "building"]


@admin.register(Expenditure)
class ExpenditureAdmin(_CsvImportExportAdmin):
    resource_classes = [ExpenditureResource]
    list_display = ["facility", "measure", "fiscal_year", "kind", "amount", "source", "as_of"]
    list_filter = ["fiscal_year", "kind", "facility__category"]
    search_fields = ["facility__name", "measure__title", "source"]
    list_select_related = ["facility", "measure"]
    autocomplete_fields = ["facility", "measure"]
