from __future__ import annotations

from unirules.core.conditions import Context
from unirules.core.rules import RuleSet, V

__all__ = ["validate_context"]


def validate_context(ruleset: RuleSet[V], ctx: Context) -> Context:
    """Validate that context values satisfy all conditions in a ruleset."""

    if not ctx:
        return ctx

    normalized: dict[str, object] = dict(ctx)
    seen_names: set[str] = set()
    for field in ruleset.iter_field_refs():
        name = field.name
        if name in seen_names or name not in ctx:
            continue
        seen_names.add(name)
        normalized[name] = field.normalize_value(ctx[name], role="Context value")
    return normalized
