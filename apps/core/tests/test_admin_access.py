import importlib
from collections.abc import Callable, Iterator

import pytest
from django.test import Client
from django.urls import clear_url_caches
from pytest_django.fixtures import Settings

import config.urls


def _reload_urls() -> None:
    """Die URL-Liste wird beim Import gebaut; nach Änderung von DEMO_MODE neu laden."""
    clear_url_caches()
    importlib.reload(config.urls)


@pytest.fixture
def demo_mode(settings: Settings) -> Iterator[Callable[[bool], None]]:
    def _set(enabled: bool) -> None:
        settings.DEMO_MODE = enabled
        _reload_urls()

    yield _set
    settings.DEMO_MODE = False
    _reload_urls()


def test_admin_is_unreachable_without_demo_mode(
    client: Client, demo_mode: Callable[[bool], None]
) -> None:
    demo_mode(False)

    assert client.get("/admin/").status_code == 404


def test_admin_is_reachable_in_demo_mode(client: Client, demo_mode: Callable[[bool], None]) -> None:
    demo_mode(True)

    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]
