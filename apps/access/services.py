"""Fachlogik für den Zugang: Codes erzeugen, einlösen, Fehlversuche begrenzen.

Bis zur Teamabstimmung ist der Code zugleich der Login (zurückgestellt: Gerätebindung,
Druckexport, Sperren). Wer einen eingelösten Code erneut eingibt, landet im selben Zugang.
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from pathlib import Path

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.access.codes import generate_code, hash_code, keyed_hash, normalize_code
from apps.access.models import AccessCode, AccessCodeStatus, FailedAttempt, Participant
from apps.access.signals import participant_active_again


class RedeemError(Enum):
    LOCKED_OUT = "Zu viele Fehlversuche. Bitte versuche es in einer Stunde erneut."
    INVALID_FORMAT = "Ein Code hat 16 Zeichen, z. B. ABCD-EFGH-JKMN-PQRS."
    UNKNOWN = "Diesen Code kennen wir nicht. Bitte prüfe die Eingabe."
    BLOCKED = "Dieser Code ist gesperrt. Bitte wende dich an deine Stadtverwaltung."


@dataclass(frozen=True)
class RedeemResult:
    participant: Participant | None = None
    error: RedeemError | None = None


@dataclass(frozen=True)
class IssuedCode:
    """Ein frisch erzeugter Code. Der Klartext existiert nur in diesem Objekt."""

    serial: str
    code: str


def create_codes(count: int, *, batch: str) -> list[IssuedCode]:
    plaintexts = [generate_code() for _ in range(count)]
    return create_codes_from(plaintexts, batch=batch)


def create_codes_from(plaintexts: list[str], *, batch: str) -> list[IssuedCode]:
    """Legt Codes mit bekanntem Klartext an (für Demo-Codes) und gibt Seriennummern zurück."""
    with transaction.atomic():
        codes = AccessCode.objects.bulk_create(
            AccessCode(code_hash=hash_code(code), batch=batch) for code in plaintexts
        )
    pairs = zip(codes, plaintexts, strict=True)
    return [IssuedCode(serial=code.serial, code=text) for code, text in pairs]


def redeem_code(raw_code: str, *, client: str) -> RedeemResult:
    """Löst einen Code ein oder meldet sich mit einem bereits eingelösten Code an."""
    with transaction.atomic():
        # Parallele Versuche desselben Clients nacheinander, sonst liefe die Sperre ins Leere.
        _lock_client(client)
        if is_locked_out(client):
            return RedeemResult(error=RedeemError.LOCKED_OUT)

        code = normalize_code(raw_code)
        if code is None:
            return _fail(client, RedeemError.INVALID_FORMAT)

        access_code = (
            AccessCode.objects.select_for_update().filter(code_hash=hash_code(code)).first()
        )
        if access_code is None:
            return _fail(client, RedeemError.UNKNOWN)
        if access_code.status == AccessCodeStatus.BLOCKED:
            return _fail(client, RedeemError.BLOCKED)
        return RedeemResult(participant=_participant_for(access_code))


def _participant_for(access_code: AccessCode) -> Participant:
    now = timezone.now()
    if access_code.status == AccessCodeStatus.ISSUED:
        access_code.status = AccessCodeStatus.REDEEMED
        access_code.redeemed_at = now
        access_code.save(update_fields=["status", "redeemed_at"])
    participant, _ = Participant.objects.get_or_create(
        access_code=access_code, defaults={"last_active_at": now}
    )
    return participant


def active_participant(participant_id: int) -> Participant | None:
    """Zugang zur Sitzung, sofern der Code nicht gesperrt ist; aktualisiert die Aktivität."""
    participant = (
        Participant.objects.select_related("access_code")
        .exclude(access_code__status=AccessCodeStatus.BLOCKED)
        .filter(pk=participant_id)
        .first()
    )
    if participant is not None:
        _touch(participant)
    return participant


def _touch(participant: Participant) -> None:
    """Höchstens ein Schreibzugriff pro Tag; Grundlage für den Verfall nach ADR-003."""
    now = timezone.now()
    previous = participant.last_active_at
    if timezone.localdate(previous) < timezone.localdate(now):
        participant_active_again.send(
            sender=Participant, participant=participant, previous_active_at=previous
        )
        participant.last_active_at = now
        participant.save(update_fields=["last_active_at"])


def is_locked_out(client: str) -> bool:
    since = timezone.now() - _lockout_window()
    attempts = FailedAttempt.objects.filter(client_hash=_client_hash(client), created_at__gte=since)
    return attempts.count() >= settings.ACCESS_MAX_FAILED_ATTEMPTS


def _fail(client: str, error: RedeemError) -> RedeemResult:
    FailedAttempt.objects.filter(created_at__lt=timezone.now() - _lockout_window()).delete()
    FailedAttempt.objects.create(client_hash=_client_hash(client))
    return RedeemResult(error=error)


def _lock_client(client: str) -> None:
    """PostgreSQL-Advisory-Lock bis zum Ende der Transaktion, je Client-Hash."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [_client_hash(client)])


def _client_hash(client: str) -> str:
    return keyed_hash(client, purpose="client")


def _lockout_window() -> timedelta:
    return timedelta(minutes=settings.ACCESS_LOCKOUT_MINUTES)


DEMO_BATCH = "Demo"


def demo_codes_missing() -> bool:
    return not AccessCode.objects.exists()


def load_demo_codes(path: Path) -> int:
    """Liest einen Code pro Zeile; Leerzeilen und Kommentare (#) werden übersprungen."""
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = [line.strip() for line in lines if line.strip() and not line.startswith("#")]
    codes = [normalize_code(entry) for entry in entries]
    invalid = [entry for entry, code in zip(entries, codes, strict=True) if code is None]
    if invalid:
        raise ValueError(f"Ungültige Demo-Codes: {', '.join(invalid)}")
    return len(create_codes_from([code for code in codes if code], batch=DEMO_BATCH))
