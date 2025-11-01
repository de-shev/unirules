from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Generic, Mapping, TypeVar

from unirules.core.conditions import Cond
from unirules.core.domains import Domain

DomainT_co = TypeVar("DomainT_co", bound=Domain, covariant=True)


class FieldRef(ABC, Generic[DomainT_co]):
    """Reference to a field in the context.

    Subclasses specialize the domain type for discrete and interval cases.
    """

    name: str
    domain: DomainT_co

    @abstractmethod
    def validate_value(self, value: object, *, role: str) -> None:
        """Validate a value against the field domain."""

    def normalize_value(self, value: object, *, role: str) -> object:
        """Validate and, if necessary, coerce a value for this field."""

        self.validate_value(value, role=role)
        return value

    def validate_context(self, ctx: Mapping[str, object]) -> None:
        """Validate a context value for this field if present."""

        if self.name not in ctx:
            return
        self.normalize_value(ctx[self.name], role="Context value")


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
