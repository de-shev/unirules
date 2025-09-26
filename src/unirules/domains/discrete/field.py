from __future__ import annotations

from typing import Any, ClassVar, Iterable

from unirules.core.conditions import Cond
from unirules.core.fields import Field
from unirules.domains.common.conditions import Eq
from unirules.domains.discrete.conditions import DiscreteCond, In_, NotIn_
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.discrete.field_ref import DiscreteFieldRef


class DiscreteField(Field[DiscreteDomain]):
    """A discrete field with a name and domain for building conditions.

    Exposes set-based operators: in_/not_in and their aliases.
    """

    __hash__: ClassVar[None] = None  # type: ignore[assignment]

    def __init__(self, name: str, domain: DiscreteDomain):
        self.name = name
        self.domain = domain

    def __eq__(self, other: object) -> Cond:  # type: ignore[override]
        """Create an equality condition.

        Args:
            other (object): The value to compare with.

        Returns:
            Cond: Equality condition referencing this field.
        """
        return Eq(DiscreteFieldRef(self.name, self.domain), other)

    def isin(self, items: Iterable[Any]) -> DiscreteCond:
        """Create an ``IN`` condition for discrete domains.

        Args:
            items (Iterable[Any]): Items that satisfy the condition.

        Returns:
            DiscreteCond: Membership condition referencing this field.
        """
        return In_(DiscreteFieldRef(self.name, self.domain), frozenset(items))

    def notin(self, items: Iterable[Any]) -> DiscreteCond:
        """Create a ``NOT IN`` condition for discrete domains.

        Args:
            items (Iterable[Any]): Items that violate the condition.

        Returns:
            DiscreteCond: Non-membership condition referencing this field.
        """
        return NotIn_(DiscreteFieldRef(self.name, self.domain), frozenset(items))


__all__ = ["DiscreteField"]
