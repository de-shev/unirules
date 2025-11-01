from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import cast

from unirules.core.conditions import Cond, CondVisitor, Context, R_co
from unirules.domains.interval.field_ref import IntervalFieldRef


@dataclass(frozen=True)
class IntervalCond(Cond, ABC):
    field: IntervalFieldRef

    def iter_field_refs(self):
        yield self.field


@dataclass(frozen=True)
class Between(IntervalCond):
    """Condition checking if a field value lies within a specified range."""

    lo: float
    hi: float
    closed: str = "both"  # "both" | "left" | "right" | "none"
    left_closed: bool = dataclass_field(init=False, repr=False, compare=False)
    right_closed: bool = dataclass_field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.closed not in {"both", "left", "right", "none"}:
            raise ValueError(
                f"Invalid closed value {self.closed!r} for field '{self.field.name}'",
            )
        original_lo = self.lo
        original_hi = self.hi
        lo = self.field.coerce(original_lo, role="Lower bound")
        hi = self.field.coerce(original_hi, role="Upper bound")
        if hi < lo:
            raise ValueError(
                f"Lower bound {original_lo!r} exceeds upper bound {original_hi!r} for field '{self.field.name}'",
            )
        object.__setattr__(self, "lo", lo)
        object.__setattr__(self, "hi", hi)
        object.__setattr__(self, "left_closed", self.closed in ("left", "both"))
        object.__setattr__(self, "right_closed", self.closed in ("right", "both"))

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is within the specified range.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the value falls within the configured range;
            ``False`` otherwise.
        """
        if self.field.name not in ctx:
            return False
        v = cast(float, ctx[self.field.name])
        lo = self.lo
        hi = self.hi
        left_ok = v > lo if self.left_closed else v >= lo
        right_ok = v < hi if self.right_closed else v <= hi
        return left_ok and right_ok

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_between(self)


@dataclass(frozen=True)
class Gt(IntervalCond):
    """Condition checking if a field value is greater than a specific value."""

    value: float

    def __post_init__(self) -> None:
        value = self.field.coerce(self.value, role="Condition value")
        object.__setattr__(self, "value", value)

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is greater than ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is greater than ``value``;
            ``False`` otherwise.
        """
        if self.field.name not in ctx:
            return False
        v = cast(float, ctx[self.field.name])
        return v > self.value

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_gt(self)


@dataclass(frozen=True)
class Ge(IntervalCond):
    """Condition checking if a field value is greater than or equal to a specific value."""

    value: float

    def __post_init__(self) -> None:
        value = self.field.coerce(self.value, role="Condition value")
        object.__setattr__(self, "value", value)

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is at least ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is greater than or equal to
            ``value``; ``False`` otherwise.
        """
        if self.field.name not in ctx:
            return False
        v = cast(float, ctx[self.field.name])
        return v >= self.value

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_ge(self)


@dataclass(frozen=True)
class Lt(IntervalCond):
    """Condition checking if a field value is less than a specific value."""

    value: float

    def __post_init__(self) -> None:
        value = self.field.coerce(self.value, role="Condition value")
        object.__setattr__(self, "value", value)

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is less than ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is less than ``value``;
            ``False`` otherwise.
        """
        if self.field.name not in ctx:
            return False
        v = cast(float, ctx[self.field.name])
        return v < self.value

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_lt(self)


@dataclass(frozen=True)
class Le(IntervalCond):
    """Condition checking if a field value is less than or equal to a specific value."""

    value: float

    def __post_init__(self) -> None:
        value = self.field.coerce(self.value, role="Condition value")
        object.__setattr__(self, "value", value)

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is at most ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is less than or equal to
            ``value``; ``False`` otherwise.
        """
        if self.field.name not in ctx:
            return False
        v = cast(float, ctx[self.field.name])
        return v <= self.value

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_le(self)


__all__ = ["IntervalCond", "Between", "Gt", "Ge", "Lt", "Le"]
