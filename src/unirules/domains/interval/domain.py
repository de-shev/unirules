from __future__ import annotations

from typing import Union

from unirules.core.domains import Domain
from unirules.domains.interval.values import IntervalSet


class IntervalDomain(Domain):
    """A domain representing a continuous interval."""

    def __init__(self, lo: Union[float, int], hi: Union[float, int]):
        """Initialize with a lower and upper bound.

        Args:
            lo (Union[float, int]): Lower bound of the interval.
            hi (Union[float, int]): Upper bound of the interval.
        """
        self.lo: float = float(lo)
        self.hi: float = float(hi)

    def get_universe(self) -> IntervalSet:
        """Return the universe of this domain.

        Returns:
            IntervalSet: Domain containing the full interval span.
        """
        return IntervalSet([(self.lo, self.hi, "none")])


__all__ = ["IntervalDomain"]
