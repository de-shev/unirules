from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any

from unirules.core.conditions import Cond, CondVisitor, Context, R_co
from unirules.domains.discrete.field_ref import DiscreteFieldRef


@dataclass(frozen=True)
class DiscreteCond(Cond, ABC):
    field: DiscreteFieldRef


@dataclass(frozen=True)
class In_(DiscreteCond):
    """Condition checking if a field value is in a set of items."""

    items: frozenset[Any]

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is in the specified set of items.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is among ``items``; ``False``
            otherwise.
        """
        return ctx.get(self.field.name) in self.items

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_in(self)


@dataclass(frozen=True)
class NotIn_(DiscreteCond):
    """Condition checking if a field value is not in a set of items."""

    items: frozenset[Any]

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value is outside the specified items.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value is not among ``items``;
            ``False`` otherwise.
        """
        return ctx.get(self.field.name) not in self.items

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_notin(self)


__all__ = ["DiscreteCond", "In_", "NotIn_"]
