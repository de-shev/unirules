from __future__ import annotations

from dataclasses import dataclass

from unirules.core.fields import FieldRef
from unirules.domains.interval.domain import IntervalDomain


@dataclass(frozen=True)
class IntervalFieldRef(FieldRef[IntervalDomain]):
    name: str
    domain: IntervalDomain


__all__ = ["IntervalFieldRef"]
