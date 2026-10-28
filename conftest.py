import importlib
from collections.abc import Callable, Iterator

import pytest
from django.urls import clear_url_caches
from pytest_django.fixtures import Settings

import config.urls


@pytest.fixture(autouse=True)
def _plain_static_storage(settings: Settings) -> None:
    """Tests brauchen kein collectstatic: einfacher Static-Storage statt Manifest."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


def _reload_urls() -> None:
    """Die URL-Liste wird beim Import gebaut; nach Änderung von DEMO_MODE neu laden."""
    clear_url_caches()
    importlib.reload(config.urls)


@pytest.fixture
def demo_mode(settings: Settings) -> Iterator[Callable[[bool], None]]:
    """Schaltet den Demo-Modus inklusive Admin-URLs um und setzt ihn danach zurück."""

    def _set(enabled: bool) -> None:
        settings.DEMO_MODE = enabled
        _reload_urls()

    yield _set
    settings.DEMO_MODE = False
    _reload_urls()
