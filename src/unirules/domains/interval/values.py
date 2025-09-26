from __future__ import annotations

from typing import Iterable

from unirules.core.domains import ValueSet

Interval = tuple[float, float, str]


class IntervalSet(ValueSet):
    """A domain representing a collection of intervals."""

    __slots__ = ("segs",)

    def __init__(self, segs: Iterable[Interval]):
        """Initialize with a collection of intervals.

        Args:
            segs (Iterable[Interval]): Iterable of ``(lo, hi, closed)`` tuples.
        """
        self.segs: list[Interval] = self._normalize(list(segs))

    @staticmethod
    def _normalize(segs: list[Interval]) -> list[Interval]:
        """Normalize a list of intervals by merging overlaps.

        Args:
            segs (list[Interval]): Intervals to normalize.

        Returns:
            list[Interval]: Non-overlapping, merged intervals.
        """
        if not segs:
            return []
        segs.sort(key=lambda s: (s[0], s[1]))
        merged: list[Interval] = [segs[0]]
        for lo, hi, closed in segs[1:]:
            lo0, hi0, c0 = merged[-1]
            if lo <= hi0:
                merged[-1] = (min(lo0, lo), max(hi0, hi), "both")
            else:
                merged.append((lo, hi, closed))
        return merged

    def union(self, other: ValueSet) -> IntervalSet:
        """Compute the union with another interval domain.

        Args:
            other (ValueSet): Another domain to combine with.

        Returns:
            IntervalSet: The union of the two domains.

        Raises:
            TypeError: If ``other`` is not an :class:`IntervalSet`.
        """
        if isinstance(other, IntervalSet):
            return IntervalSet(self.segs + other.segs)
        raise TypeError(f"Cannot union with {type(other)}")

    @staticmethod
    def _decode_closed(closed: str) -> tuple[bool, bool]:
        left = closed in ("left", "both")
        right = closed in ("right", "both")
        return left, right

    @staticmethod
    def _encode_closed(left: bool, right: bool) -> str:
        if left and right:
            return "both"
        if left:
            return "left"
        if right:
            return "right"
        return "none"

    def inter(self, other: ValueSet) -> IntervalSet:  # noqa: PLR0912
        """Compute the intersection with another interval domain.

        Args:
            other (ValueSet): Another domain to intersect with.

        Returns:
            IntervalSet: The intersection of the two domains.

        Raises:
            TypeError: If ``other`` is not an :class:`IntervalSet`.
        """

        if isinstance(other, IntervalSet):
            res: list[Interval] = []
            a = self.segs
            b = other.segs
            i = j = 0
            while i < len(a) and j < len(b):
                alo, ahi, ac = a[i]
                blo, bhi, bc = b[j]
                lo = max(alo, blo)
                hi = min(ahi, bhi)
                if lo < hi or (lo == hi and self._decode_closed(ac)[1] and self._decode_closed(bc)[0]):
                    a_left, a_right = self._decode_closed(ac)
                    b_left, b_right = self._decode_closed(bc)
                    if lo == alo == blo:
                        left_closed = a_left and b_left
                    elif lo == alo:
                        left_closed = a_left
                    elif lo == blo:
                        left_closed = b_left
                    else:
                        left_closed = True

                    if hi == ahi == bhi:
                        right_closed = a_right and b_right
                    elif hi == ahi:
                        right_closed = a_right
                    elif hi == bhi:
                        right_closed = b_right
                    else:
                        right_closed = True

                    res.append((lo, hi, self._encode_closed(left_closed, right_closed)))
                if ahi < bhi:
                    i += 1
                else:
                    j += 1
            return IntervalSet(res)
        raise TypeError(f"Cannot intersect with {type(other)}")

    def diff(self, other: ValueSet) -> IntervalSet:
        """Compute the difference with another interval domain.

        Args:
            other (ValueSet): Another domain to subtract.

        Returns:
            IntervalSet: The difference of the two domains.

        Raises:
            TypeError: If ``other`` is not an :class:`IntervalSet`.
        """
        if isinstance(other, IntervalSet):
            result = self.segs[:]
            for o_lo, o_hi, _ in other.segs:
                new: list[Interval] = []
                for lo, hi, c in result:
                    if o_hi <= lo or o_lo >= hi:
                        new.append((lo, hi, c))
                    else:
                        if lo < o_lo:
                            new.append((lo, o_lo, c))
                        if o_hi < hi:
                            new.append((o_hi, hi, c))
                result = new
            return IntervalSet(result)
        raise TypeError(f"Cannot diff with {type(other)}")

    def complement(self, universe: ValueSet) -> IntervalSet:
        """Compute the complement with respect to an interval universe.

        Args:
            universe (ValueSet): The universe domain.

        Returns:
            IntervalSet: The complement of this domain.

        Raises:
            TypeError: If ``universe`` is not an :class:`IntervalSet`.
        """
        if isinstance(universe, IntervalSet):
            return universe.diff(self)
        raise TypeError(f"Cannot complement wrt {type(universe)}")

    def is_empty(self) -> bool:
        """Check if the domain is empty.

        Returns:
            bool: ``True`` if the domain has no intervals, ``False`` otherwise.
        """
        return not self.segs

    def __repr__(self) -> str:
        """Return a string representation of the domain."""
        return f"Intervals({self.segs!r})"


__all__ = ["Interval", "IntervalSet"]
