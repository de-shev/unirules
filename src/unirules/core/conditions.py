from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, TypeVar

from typing_extensions import Protocol

R_co = TypeVar("R_co", covariant=True)

if TYPE_CHECKING:
    from unirules.domains.common.conditions import Eq
    from unirules.domains.discrete.conditions import In_, NotIn_
    from unirules.domains.interval.conditions import Between, Ge, Gt, Le, Lt


Context = Mapping[str, object]

__all__ = ["Context", "CondVisitor", "Cond", "And", "Or", "Not", "AlwaysTrue", "R_co"]


class CondVisitor(Protocol[R_co]):
    def visit_and(self, cond: "And") -> R_co: ...

    def visit_or(self, cond: "Or") -> R_co: ...

    def visit_not(self, cond: "Not") -> R_co: ...

    def visit_always_true(self, cond: "AlwaysTrue") -> R_co: ...

    def visit_eq(self, cond: "Eq") -> R_co: ...

    def visit_in(self, cond: "In_") -> R_co: ...

    def visit_notin(self, cond: "NotIn_") -> R_co: ...

    def visit_between(self, cond: "Between") -> R_co: ...

    def visit_gt(self, cond: "Gt") -> R_co: ...

    def visit_ge(self, cond: "Ge") -> R_co: ...

    def visit_lt(self, cond: "Lt") -> R_co: ...

    def visit_le(self, cond: "Le") -> R_co: ...


class Cond(ABC):
    """Base class for conditions in the rule evaluation system."""

    @abstractmethod
    def eval(self, ctx: Context) -> bool:
        """Evaluate the condition against a context dictionary.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: The result of the condition evaluation.
        """
        raise NotImplementedError

    # Visitor support
    @abstractmethod
    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        """Accept a visitor implementing the projection logic.

        Args:
            visitor (CondVisitor[R_co]): The visitor instance to accept.

        Returns:
            R_co: The result produced by the visitor.
        """
        raise NotImplementedError

    def __and__(self, other: Cond) -> Cond:
        """Return an :class:`And` condition combining two operands."""
        return And(self, other)

    def __or__(self, other: Cond) -> Cond:
        """Return an :class:`Or` condition combining two operands."""
        return Or(self, other)

    def __invert__(self) -> Cond:
        """Return a :class:`Not` condition negating this operand."""
        return Not(self)


@dataclass(frozen=True)
class And(Cond):
    """Condition combining two conditions with logical AND."""

    a: Cond
    b: Cond

    def eval(self, ctx: Context) -> bool:
        """Evaluate both conditions with logical ``AND``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if both conditions evaluate to ``True``; ``False``
            otherwise.
        """
        return self.a.eval(ctx) and self.b.eval(ctx)

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_and(self)


@dataclass(frozen=True)
class Or(Cond):
    """Condition combining two conditions with logical OR."""

    a: Cond
    b: Cond

    def eval(self, ctx: Context) -> bool:
        """Evaluate both conditions with logical ``OR``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if at least one condition evaluates to ``True``;
            ``False`` otherwise.
        """
        return self.a.eval(ctx) or self.b.eval(ctx)

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_or(self)


@dataclass(frozen=True)
class Not(Cond):
    """Condition negating another condition."""

    a: Cond

    def eval(self, ctx: Context) -> bool:
        """Evaluate the negated condition.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the wrapped condition evaluates to ``False``;
            ``False`` otherwise.
        """
        return not self.a.eval(ctx)

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_not(self)


@dataclass(frozen=True)
class AlwaysTrue(Cond):
    """A condition that always evaluates to True."""

    def eval(self, ctx: Context) -> bool:
        """Always return ``True``.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: Always ``True``.
        """
        return True

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_always_true(self)
