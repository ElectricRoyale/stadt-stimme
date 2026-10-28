"""Aktivierungscodes: Erzeugen, Normalisieren und Hashen (ADR-001).

Ein Code hat 16 Zeichen Crockford-Base32 (80 Bit Zufall) und wird in 4er-Gruppen gedruckt.
Gespeichert wird nur ein HMAC-SHA256 mit geheimem Schlüssel. Ein langsamer Passwort-Hash ist
nicht nötig: Bei 80 Bit Zufall scheitert Raten auch ohne Rate-Limit an der Menge, und der
Schlüssel verhindert, dass ein Datenbank-Abzug allein zum Prüfen von Codes reicht.
"""

import hashlib
import hmac
import secrets

from django.conf import settings

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CODE_LENGTH = 16
GROUP_SIZE = 4

# Crockford-Base32 liest verwechselbare Zeichen tolerant; U kommt im Alphabet nicht vor.
_CONFUSABLES = str.maketrans({"O": "0", "I": "1", "L": "1"})
_SEPARATORS = str.maketrans("", "", " -\t")


def generate_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


def normalize_code(raw: str) -> str | None:
    """Großschreibung, Trennzeichen entfernen, Verwechsler ersetzen. None bei falschem Format."""
    code = raw.upper().translate(_SEPARATORS).translate(_CONFUSABLES)
    if len(code) != CODE_LENGTH or any(char not in ALPHABET for char in code):
        return None
    return code


def format_code(code: str) -> str:
    return "-".join(code[i : i + GROUP_SIZE] for i in range(0, len(code), GROUP_SIZE))


def keyed_hash(value: str, *, purpose: str) -> str:
    """HMAC-SHA256 mit dem Code-Schlüssel; ``purpose`` trennt Codes von IP-Adressen."""
    key = settings.ACCESS_CODE_PEPPER.encode()
    return hmac.new(key, f"{purpose}:{value}".encode(), hashlib.sha256).hexdigest()


def hash_code(code: str) -> str:
    return keyed_hash(code, purpose="code")
