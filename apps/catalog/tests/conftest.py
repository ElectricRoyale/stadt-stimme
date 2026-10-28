import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from django.conf import settings


@pytest.fixture
def demo_copy(tmp_path: Path) -> Path:
    """Beschreibbare Kopie der Demo-Daten für Fehlerfälle."""
    target = tmp_path / "catalog"
    shutil.copytree(settings.DEMO_DATA_DIR, target, ignore=shutil.ignore_patterns("*.md"))
    return target


@pytest.fixture
def replace_in(demo_copy: Path) -> Callable[[str, str, str], Path]:
    """Ersetzt Text in einer CSV-Datei der Kopie und gibt das Verzeichnis zurück."""

    def _replace(filename: str, old: str, new: str) -> Path:
        path = demo_copy / filename
        content = path.read_text(encoding="utf-8")
        assert old in content, f"{old!r} nicht in {filename}"
        path.write_text(content.replace(old, new, 1), encoding="utf-8")
        return demo_copy

    return _replace
