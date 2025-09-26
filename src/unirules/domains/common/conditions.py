from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from unirules.core.conditions import Cond, CondVisitor, Context, R_co
from unirules.core.domains import Domain
from unirules.core.fields import FieldRef


@dataclass(frozen=True)
class Eq(Cond):
    """Condition checking if a field equals a specific value."""

    field: FieldRef[Domain]
    value: Any

    def eval(self, ctx: Context) -> bool:
        """Evaluate whether the field value equals the specified value.

        Args:
            ctx (Context): A mapping of field names to their values.

        Returns:
            bool: ``True`` if the field value equals ``value``; ``False``
            otherwise.
        """
        return ctx.get(self.field.name) == self.value

    def accept(self, visitor: CondVisitor[R_co]) -> R_co:
        return visitor.visit_eq(self)


__all__ = ["Eq"]
