from __future__ import annotations

from dataclasses import dataclass

from unirules.core.fields import FieldRef
from unirules.domains.discrete.domain import DiscreteDomain


@dataclass(frozen=True)
class DiscreteFieldRef(FieldRef[DiscreteDomain]):
    name: str
    domain: DiscreteDomain

    def validate_value(self, value: object, *, role: str) -> None:
        try:
            if value not in self.domain.vals:
                raise ValueError(
                    f"{role} {value!r} for field '{self.name}' is not allowed",
                )
        except TypeError as exc:
            raise ValueError(
                f"{role} {value!r} for field '{self.name}' is not allowed",
            ) from exc


__all__ = ["DiscreteFieldRef"]
