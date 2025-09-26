from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any, Union, cast

from unirules.core.conditions import Cond, CondVisitor, Context, R_co
from unirules.domains.interval.field_ref import IntervalFieldRef


@dataclass(frozen=True)
class IntervalCond(Cond, ABC):
    field: IntervalFieldRef


@dataclass(frozen=True)
class Between(IntervalCond):
    """Condition checking if a field value lies within a specified range."""

    lo: Union[float, int]
    hi: Union[float, int]
    closed: str = "both"  # "both" | "left" | "right" | "none"

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is within the specified range.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the value falls within the configured range;
            ``False`` otherwise.
        """
        raw = ctx.get(self.field.name)
        try:
            v = float(cast(Any, raw))
        except (TypeError, ValueError):
            return False
        lo = float(self.lo)
        hi = float(self.hi)
        left = v > lo if self.closed in ("right", "none") else v >= lo
        right = v < hi if self.closed in ("left", "none") else v <= hi
        return left and right

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_between(self)


@dataclass(frozen=True)
class Gt(IntervalCond):
    """Condition checking if a field value is greater than a specific value."""

    value: Union[float, int]

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is greater than ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is greater than ``value``;
            ``False`` otherwise.
        """
        raw = ctx.get(self.field.name)
        try:
            v = float(cast(Any, raw))
        except (TypeError, ValueError):
            return False
        return v > float(self.value)

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_gt(self)


@dataclass(frozen=True)
class Ge(IntervalCond):
    """Condition checking if a field value is greater than or equal to a specific value."""

    value: Union[float, int]

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is at least ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is greater than or equal to
            ``value``; ``False`` otherwise.
        """
        raw = ctx.get(self.field.name)
        try:
            v = float(cast(Any, raw))
        except (TypeError, ValueError):
            return False
        return v >= float(self.value)

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_ge(self)


@dataclass(frozen=True)
class Lt(IntervalCond):
    """Condition checking if a field value is less than a specific value."""

    value: Union[float, int]

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is less than ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is less than ``value``;
            ``False`` otherwise.
        """
        raw = ctx.get(self.field.name)
        try:
            v = float(cast(Any, raw))
        except (TypeError, ValueError):
            return False
        return v < float(self.value)

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_lt(self)


@dataclass(frozen=True)
class Le(IntervalCond):
    """Condition checking if a field value is less than or equal to a specific value."""

    value: Union[float, int]

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is at most ``value``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is less than or equal to
            ``value``; ``False`` otherwise.
        """
        raw = ctx.get(self.field.name)
        try:
            v = float(cast(Any, raw))
        except (TypeError, ValueError):
            return False
        return v <= float(self.value)

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_le(self)


__all__ = ["IntervalCond", "Between", "Gt", "Ge", "Lt", "Le"]
