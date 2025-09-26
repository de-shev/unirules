from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar

from unirules.core.conditions import Cond
from unirules.core.domains import Domain

DomainT_co = TypeVar("DomainT_co", bound=Domain, covariant=True)


class FieldRef(ABC, Generic[DomainT_co]):
    """Reference to a field in the context.

    Subclasses specialize the domain type for discrete and interval cases.
    """

    name: str
    domain: DomainT_co


class Field(ABC, Generic[DomainT_co]):
    __hash__: ClassVar[None] = None  # type: ignore[assignment]

    @abstractmethod
    def __eq__(self, other: object) -> Cond:  # type: ignore[override]
        raise NotImplementedError

    def equals(self, v: object) -> Cond:
        """Create an equality condition alias.

        Args:
            v (object): The value to compare against.

        Returns:
            Cond: An equality condition equivalent to using ``==``.
        """
        return self == v


__all__ = ["FieldRef", "Field", "DomainT_co"]
