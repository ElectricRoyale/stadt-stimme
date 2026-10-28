"""CSV-Zuordnung für den Katalog-Import (django-import-export).

Spaltennamen entsprechen den Dateien in data/demo. Verknüpft wird über die externe ID,
damit derselbe Import beliebig oft laufen kann (Upsert statt Duplikate).
"""

from typing import Any

from django.db import models
from import_export import fields, resources, widgets

from apps.catalog.models import (
    Building,
    Category,
    Expenditure,
    ExpenditureKind,
    Facility,
    Measure,
    MeasureStatus,
)


class ChoiceWidget(widgets.Widget):
    """Akzeptiert Wert oder Anzeigenamen einer Auswahl, ohne Groß-/Kleinschreibung."""

    def __init__(self, choices: type[models.TextChoices], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._choices = choices
        self._lookup = {}
        for value, label in choices.choices:
            self._lookup[str(value).casefold()] = value
            self._lookup[str(label).casefold()] = value

    def clean(self, value: Any, row: Any = None, **kwargs: Any) -> str:
        key = str(value or "").strip().casefold()
        if key not in self._lookup:
            allowed = ", ".join(str(label) for label in self._choices.labels)
            raise ValueError(f"Unbekannter Wert {value!r}. Erlaubt: {allowed}.")
        return str(self._lookup[key])

    def render(self, value: Any, obj: Any = None, **kwargs: Any) -> str:
        return str(self._choices(value).label) if value else ""


class ExternalIdWidget(widgets.ForeignKeyWidget):
    """Verweis über die externe ID; ein unbekannter Schlüssel wird zum Zeilenfehler."""

    def __init__(self, model: type[models.Model], *, required: bool = True) -> None:
        super().__init__(model, field="external_id")
        self._required = required

    def clean(self, value: Any, row: Any = None, **kwargs: Any) -> Any:
        key = str(value or "").strip()
        if not key:
            if self._required:
                raise ValueError("Pflichtfeld ist leer.")
            return None
        try:
            return self.model.objects.get(external_id=key)
        except self.model.DoesNotExist as error:
            raise ValueError(
                f"{self.model._meta.verbose_name} mit ID {key!r} nicht gefunden."
            ) from error


class CategoryNameWidget(widgets.ForeignKeyWidget):
    """Kategorie über den Namen; unbekannte Kategorien werden angelegt."""

    def __init__(self) -> None:
        super().__init__(Category, field="name")

    def clean(self, value: Any, row: Any = None, **kwargs: Any) -> Category:
        name = str(value or "").strip()
        if not name:
            raise ValueError("Kategorie ist leer.")
        category, _ = Category.objects.get_or_create(name=name)
        return category


class _CatalogResource(resources.ModelResource):
    class Meta:
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True


class FacilityResource(_CatalogResource):
    category = fields.Field(
        attribute="category", column_name="category", widget=CategoryNameWidget()
    )

    class Meta(_CatalogResource.Meta):
        model = Facility
        import_id_fields = ["external_id"]
        fields = ["external_id", "name", "category", "address", "description"]


class BuildingResource(_CatalogResource):
    facility = fields.Field(
        attribute="facility",
        column_name="facility_external_id",
        widget=ExternalIdWidget(Facility),
    )

    class Meta(_CatalogResource.Meta):
        model = Building
        import_id_fields = ["external_id"]
        fields = ["external_id", "facility", "name", "address", "description"]


class MeasureResource(_CatalogResource):
    facility = fields.Field(
        attribute="facility",
        column_name="facility_external_id",
        widget=ExternalIdWidget(Facility),
    )
    building = fields.Field(
        attribute="building",
        column_name="building_external_id",
        widget=ExternalIdWidget(Building, required=False),
    )
    status = fields.Field(
        attribute="status", column_name="status", widget=ChoiceWidget(MeasureStatus)
    )

    class Meta(_CatalogResource.Meta):
        model = Measure
        import_id_fields = ["external_id"]
        fields = ["external_id", "facility", "building", "title", "description", "status"]


class ExpenditureResource(_CatalogResource):
    facility = fields.Field(
        attribute="facility",
        column_name="facility_external_id",
        widget=ExternalIdWidget(Facility),
    )
    measure = fields.Field(
        attribute="measure",
        column_name="measure_external_id",
        widget=ExternalIdWidget(Measure, required=False),
    )
    amount = fields.Field(
        attribute="amount", column_name="amount_eur", widget=widgets.DecimalWidget()
    )
    kind = fields.Field(attribute="kind", column_name="kind", widget=ChoiceWidget(ExpenditureKind))
    as_of = fields.Field(
        attribute="as_of", column_name="as_of", widget=widgets.DateWidget(format="%Y-%m-%d")
    )

    class Meta(_CatalogResource.Meta):
        model = Expenditure
        import_id_fields = ["facility", "measure", "fiscal_year", "kind"]
        fields = ["facility", "measure", "fiscal_year", "amount", "kind", "source", "as_of"]
