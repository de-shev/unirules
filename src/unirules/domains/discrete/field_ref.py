from __future__ import annotations

from dataclasses import dataclass

from unirules.core.fields import FieldRef
from unirules.domains.discrete.domain import DiscreteDomain


@dataclass(frozen=True)
class DiscreteFieldRef(FieldRef[DiscreteDomain]):
    name: str
    domain: DiscreteDomain


__all__ = ["DiscreteFieldRef"]
