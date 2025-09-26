from __future__ import annotations

from typing import Any, Iterable

from unirules.core.domains import ValueSet


class DiscreteSet(ValueSet):
    """A domain representing a discrete set of values."""

    __slots__ = ("vals",)

    def __init__(self, vals: Iterable[Any]):
        """Initialize with a set of values.

        Args:
            vals (Iterable[Any]): Values describing the discrete domain.
        """
        self.vals: frozenset[Any] = frozenset(vals)

    def union(self, other: ValueSet) -> DiscreteSet:
        """Compute the union with another discrete domain.

        Args:
            other (ValueSet): Another domain to combine with.

        Returns:
            DiscreteSet: The union of the two domains.

        Raises:
            TypeError: If ``other`` is not a :class:`DiscreteSet`.
        """
        if isinstance(other, DiscreteSet):
            return DiscreteSet(self.vals | other.vals)
        raise TypeError(f"Cannot union with {type(other)}")

    def inter(self, other: ValueSet) -> DiscreteSet:
        """Compute the intersection with another discrete domain.

        Args:
            other (ValueSet): Another domain to intersect with.

        Returns:
            DiscreteSet: The intersection of the two domains.

        Raises:
            TypeError: If ``other`` is not a :class:`DiscreteSet`.
        """
        if isinstance(other, DiscreteSet):
            return DiscreteSet(self.vals & other.vals)
        raise TypeError(f"Cannot intersect with {type(other)}")

    def diff(self, other: ValueSet) -> DiscreteSet:
        """Compute the difference with another discrete domain.

        Args:
            other (ValueSet): Another domain to subtract.

        Returns:
            DiscreteSet: The difference of the two domains.

        Raises:
            TypeError: If ``other`` is not a :class:`DiscreteSet`.
        """
        if isinstance(other, DiscreteSet):
            return DiscreteSet(self.vals - other.vals)
        raise TypeError(f"Cannot diff with {type(other)}")

    def complement(self, universe: ValueSet) -> DiscreteSet:
        """Compute the complement with respect to a discrete universe.

        Args:
            universe (ValueSet): The universe domain.

        Returns:
            DiscreteSet: The complement of this domain.

        Raises:
            TypeError: If ``universe`` is not a :class:`DiscreteSet`.
        """
        if isinstance(universe, DiscreteSet):
            return DiscreteSet(universe.vals - self.vals)
        raise TypeError(f"Cannot complement wrt {type(universe)}")

    def is_empty(self) -> bool:
        """Check if the domain is empty.

        Returns:
            bool: ``True`` if the domain has no values, ``False`` otherwise.
        """
        return not self.vals

    def __repr__(self) -> str:
        """Return a string representation of the domain."""
        return f"Discrete({sorted(self.vals)!r})"


__all__ = ["DiscreteSet"]
