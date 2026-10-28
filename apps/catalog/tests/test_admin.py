from collections.abc import Callable

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.catalog.models import Facility
from apps.catalog.services import import_catalog

pytestmark = pytest.mark.django_db

MODELS = ["category", "facility", "measure", "expenditure"]


@pytest.fixture
def admin_client_in_demo(client: Client, demo_mode: Callable[[bool], None]) -> Client:
    demo_mode(True)
    import_catalog(settings.DEMO_DATA_DIR)
    user = get_user_model().objects.create_superuser("markus", password="test-passwort")
    client.force_login(user)
    return client


@pytest.mark.parametrize("model", MODELS)
def test_changelist_shows_demo_data(admin_client_in_demo: Client, model: str) -> None:
    response = admin_client_in_demo.get(f"/admin/catalog/{model}/")

    assert response.status_code == 200


@pytest.mark.parametrize("model", ["facility", "measure", "expenditure"])
def test_csv_import_page_is_available(admin_client_in_demo: Client, model: str) -> None:
    response = admin_client_in_demo.get(f"/admin/catalog/{model}/import/")

    assert response.status_code == 200


def test_facility_change_page_lists_measures(admin_client_in_demo: Client) -> None:
    pool = Facility.objects.get(external_id="E-001")

    response = admin_client_in_demo.get(f"/admin/catalog/facility/{pool.pk}/change/")

    assert "Sanierung Hallendach" in response.content.decode()


def test_csv_upload_shows_preview_before_saving(
    client: Client, demo_mode: Callable[[bool], None]
) -> None:
    demo_mode(True)
    client.force_login(get_user_model().objects.create_superuser("markus", password="pw-1234"))
    upload = SimpleUploadedFile(
        "facilities.csv",
        (settings.DEMO_DATA_DIR / "facilities.csv").read_bytes(),
        content_type="text/csv",
    )

    response = client.post(
        "/admin/catalog/facility/import/",
        {"import_file": upload, "format": "0", "resource": "0"},
    )

    assert response.status_code == 200
    assert "Hallenbad Am Stadtpark" in response.content.decode()
    assert not Facility.objects.exists()
