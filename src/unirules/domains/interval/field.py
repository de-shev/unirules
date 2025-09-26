from __future__ import annotations

from typing import ClassVar, Union

from unirules.core.conditions import Cond
from unirules.core.fields import Field
from unirules.domains.common.conditions import Eq
from unirules.domains.interval.conditions import Between, Ge, Gt, IntervalCond, Le, Lt
from unirules.domains.interval.domain import IntervalDomain
from unirules.domains.interval.field_ref import IntervalFieldRef


class IntervalField(Field[IntervalDomain]):
    """A continuous interval field with a name and domain for building conditions.

    Exposes interval/numeric operators: between, gt/ge/lt/le and their operator forms.
    """

    __hash__: ClassVar[None] = None  # type: ignore[assignment]

    def __init__(self, name: str, domain: IntervalDomain):
        self.name = name
        self.domain = domain

    # operator forms delegate to methods
    def __eq__(self, other: object) -> Cond:  # type: ignore[override]
        """Create an equality condition.

        Args:
            other (object): The value to compare with.

        Returns:
            Cond: Equality condition referencing this field.
        """
        return Eq(IntervalFieldRef(self.name, self.domain), other)

    def __gt__(self, other: Union[float, int]) -> IntervalCond:
        return self.gt(other)

    def __ge__(self, other: Union[float, int]) -> IntervalCond:
        return self.ge(other)

    def __lt__(self, other: Union[float, int]) -> IntervalCond:
        return self.lt(other)

    def __le__(self, other: Union[float, int]) -> IntervalCond:
        return self.le(other)

    def between(self, lo: Union[float, int], hi: Union[float, int], *, closed: str = "none") -> IntervalCond:
        """Create a ``BETWEEN`` condition.

        Args:
            lo (Union[float, int]): Lower bound of the interval.
            hi (Union[float, int]): Upper bound of the interval.
            closed (str): Which bounds are closed (``"both"``, ``"left"``,
                ``"right"``, or ``"none"``).

        Returns:
            IntervalCond: Range condition referencing this field.
        """

        return Between(IntervalFieldRef(self.name, self.domain), lo, hi, closed)

    def gt(self, value: Union[float, int]) -> IntervalCond:
        """Create a strictly-greater-than condition.

        Args:
            value (Union[float, int]): Threshold for the comparison.

        Returns:
            IntervalCond: Condition representing ``field > value``.
        """

        return Gt(IntervalFieldRef(self.name, self.domain), value)

    def ge(self, value: Union[float, int]) -> IntervalCond:
        """Create a greater-or-equal-to condition.

        Args:
            value (Union[float, int]): Threshold for the comparison.

        Returns:
            IntervalCond: Condition representing ``field >= value``.
        """

        return Ge(IntervalFieldRef(self.name, self.domain), value)

    def lt(self, value: Union[float, int]) -> IntervalCond:
        """Create a strictly-less-than condition.

        Args:
            value (Union[float, int]): Threshold for the comparison.

        Returns:
            IntervalCond: Condition representing ``field < value``.
        """

        return Lt(IntervalFieldRef(self.name, self.domain), value)

    def le(self, value: Union[float, int]) -> IntervalCond:
        """Create a less-or-equal-to condition.

        Args:
            value (Union[float, int]): Threshold for the comparison.

        Returns:
            IntervalCond: Condition representing ``field <= value``.
        """

        return Le(IntervalFieldRef(self.name, self.domain), value)


__all__ = ["IntervalField"]
