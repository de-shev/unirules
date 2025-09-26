from __future__ import annotations

from abc import ABC, abstractmethod


class ValueSet(ABC):
    """Base class for field domains."""

    @abstractmethod
    def union(self, other: ValueSet) -> ValueSet:
        """Compute the union of this domain with another.

        Args:
            other (ValueSet): Another domain to combine with.

        Returns:
            ValueSet: The union of the two domains.
        """
        raise NotImplementedError

    @abstractmethod
    def inter(self, other: ValueSet) -> ValueSet:
        """Compute the intersection of this domain with another.

        Args:
            other (ValueSet): Another domain to intersect with.

        Returns:
            ValueSet: The intersection of the two domains.
        """
        raise NotImplementedError

    @abstractmethod
    def diff(self, other: ValueSet) -> ValueSet:
        """Compute the difference between this domain and another.

        Args:
            other (ValueSet): Another domain to subtract.

        Returns:
            ValueSet: The difference of the two domains.
        """
        raise NotImplementedError

    @abstractmethod
    def complement(self, universe: ValueSet) -> ValueSet:
        """Compute the complement of this domain with respect to a universe.

        Args:
            universe (ValueSet): The universe domain.

        Returns:
            ValueSet: The complement of this domain.
        """
        raise NotImplementedError

    @abstractmethod
    def is_empty(self) -> bool:
        """Check if the domain is empty.

        Returns:
            bool: ``True`` if the domain is empty, ``False`` otherwise.
        """
        raise NotImplementedError


class Domain(ABC):
    """Base class for field domains."""

    @abstractmethod
    def get_universe(self) -> ValueSet:
        """Return the universe value set for this domain."""
        pass


__all__ = ["ValueSet", "Domain"]
