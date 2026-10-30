"""Ziel von Punkten: eine Einrichtung oder ein ganzes Thema (ADR-011)."""

from dataclasses import dataclass
from typing import Literal, Protocol

TargetKind = Literal["f", "c"]


class HasTarget(Protocol):
    """Zeile mit genau einem Ziel, z. B. ``Allocation`` oder ``PointEvent``."""

    facility_id: int | None
    category_id: int | None


@dataclass(frozen=True, order=True)
class Target:
    """Ziel von Punkten: Einrichtung (``f``) oder Thema allgemein (``c``)."""

    kind: TargetKind
    pk: int

    @property
    def key(self) -> str:
        return f"{self.kind}-{self.pk}"

    @property
    def facility_id(self) -> int | None:
        return self.pk if self.kind == "f" else None

    @property
    def category_id(self) -> int | None:
        return self.pk if self.kind == "c" else None

    @classmethod
    def of(cls, row: HasTarget) -> "Target":
        if row.facility_id is not None:
            return cls("f", row.facility_id)
        if row.category_id is None:  # durch den Check-Constraint ausgeschlossen
            raise ValueError("Punkte ohne Ziel")
        return cls("c", row.category_id)
