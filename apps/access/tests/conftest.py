import pytest

from apps.access.services import IssuedCode, create_codes


@pytest.fixture
def issued(db: None) -> IssuedCode:
    """Ein frisch ausgegebener Code mit bekanntem Klartext."""
    return create_codes(1, batch="Test")[0]
