from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, cast

from unirules.core.fields import FieldRef
from unirules.domains.interval.domain import IntervalDomain


@dataclass(frozen=True)
class IntervalFieldRef(FieldRef[IntervalDomain]):
    name: str
    domain: IntervalDomain

    def coerce(self, raw: object, *, role: str) -> float:
        try:
            numeric = float(cast(Any, raw))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{role} {raw!r} for field '{self.name}' is not numeric",
            ) from exc
        if not math.isfinite(numeric):
            raise ValueError(
                f"{role} {raw!r} for field '{self.name}' is not numeric",
            )
        if numeric < self.domain.lo or numeric > self.domain.hi:
            raise ValueError(
                f"{role} {raw!r} for field '{self.name}' is outside of allowed range",
            )
        return numeric

    def validate_value(self, value: object, *, role: str) -> None:
        self.coerce(value, role=role)

    def normalize_value(self, value: object, *, role: str) -> float:
        return self.coerce(value, role=role)


__all__ = ["IntervalFieldRef"]
