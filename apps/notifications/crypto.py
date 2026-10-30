"""Symmetrische Verschlüsselung der E-Mail-Adressen (ADR-004).

Fernet (AES-128-CBC mit HMAC-SHA256) mit einem Schlüssel, der aus ``EMAIL_ADDRESS_KEY`` abgeleitet
ist. Wer nur die Datenbank hat, liest keine Adressen.
"""

import base64
import hashlib
import secrets

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    material = f"stadtstimme.notifications.email:{settings.EMAIL_ADDRESS_KEY}".encode()
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(material).digest()))


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode("ascii")


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode("ascii")).decode()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    """Bestätigungs-Token werden nur als Hash gespeichert; sie haben 256 Bit Zufall."""
    return hashlib.sha256(token.encode()).hexdigest()
