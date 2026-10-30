"""Ohne Freigabe (ADR-025): eingereichte und freigegebene Vorschläge sind beide „offen“."""

from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def open_all(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    proposal = apps.get_model("proposals", "Proposal")
    proposal.objects.filter(status__in=["eingereicht", "freigegeben"]).update(status="offen")


def back_to_released(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    proposal = apps.get_model("proposals", "Proposal")
    proposal.objects.filter(status="offen").update(status="freigegeben")


class Migration(migrations.Migration):
    dependencies = [("proposals", "0003_proposal_point")]

    operations = [
        migrations.AlterField(
            model_name="proposal",
            name="status",
            field=models.CharField(
                choices=[
                    ("offen", "Offen"),
                    ("eingereicht", "Eingereicht"),
                    ("freigegeben", "Freigegeben"),
                    ("angenommen", "Angenommen"),
                    ("abgelehnt", "Abgelehnt"),
                ],
                default="offen",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.RunPython(open_all, back_to_released),
        migrations.AlterField(
            model_name="proposal",
            name="status",
            field=models.CharField(
                choices=[("offen", "Offen"), ("angenommen", "Angenommen"), ("abgelehnt", "Abgelehnt")],
                default="offen",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.RemoveField(model_name="proposal", name="published_at"),
    ]
