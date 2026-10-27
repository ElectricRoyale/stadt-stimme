import pytest
from pytest_django.fixtures import Settings


@pytest.fixture(autouse=True)
def _plain_static_storage(settings: Settings) -> None:
    """Tests brauchen kein collectstatic: einfacher Static-Storage statt Manifest."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
