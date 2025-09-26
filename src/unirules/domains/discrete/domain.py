from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, Union

from unirules.core.domains import Domain
from unirules.domains.discrete.values import DiscreteSet


class DiscreteDomain(Domain):
    """A domain for discrete values, supporting Enum or iterable inputs."""

    def __init__(self, vals: Union[Iterable[Any], type[Enum]]):
        """Initialize the domain with concrete values or an ``Enum`` type.

        Args:
            vals (Union[Iterable[Any], type[Enum]]): Values describing the
                domain or an enumeration whose members define the domain.
        """
        if isinstance(vals, type) and issubclass(vals, Enum):
            self.vals: frozenset[Any] = frozenset(e.value for e in vals)
        else:
            self.vals = frozenset(vals)

    def get_universe(self) -> DiscreteSet:
        """Return the universe of this domain.

        Returns:
            DiscreteSet: Discrete domain containing all admissible values.
        """
        return DiscreteSet(self.vals)


__all__ = ["DiscreteDomain"]
