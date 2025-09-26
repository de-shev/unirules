from __future__ import annotations

from typing import Any, MutableMapping, Optional

from unirules.core.rules import RuleSet, RuleSetPolicy, RuleTree, RuleValue
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.interval.domain import IntervalDomain
from unirules.dsl import Else, field, otherwise, ruleset, when

__all__ = ["load_ruleset_from_code"]


def load_ruleset_from_code(
    code: str,
    *,
    ruleset_var: str = "RULESET",
    globals_dict: Optional[MutableMapping[str, Any]] = None,
    locals_dict: Optional[MutableMapping[str, Any]] = None,
    include_builtins: bool = True,
) -> RuleSet:
    """Execute ``code`` and return a :class:`RuleSet` defined in ``ruleset_var``.

    The helper populates the execution context with the DSL helpers so that
    ``code`` can define rulesets without needing to import them explicitly.

    Args:
        code (str): Source code that defines a :class:`RuleSet` instance.
        ruleset_var (str): Name of the variable that stores the resulting
            ruleset. Defaults to ``"RULESET"``.
        globals_dict (MutableMapping[str, Any] | None): Optional mapping of
            additional globals to expose to ``exec``.
        locals_dict (MutableMapping[str, Any] | None): Optional mapping to use
            for locals during ``exec``.
        include_builtins (bool): Whether to include the built-in ``__builtins__``

    Returns:
        RuleSet[V]: The ruleset defined by ``code``.

    Raises:
        KeyError: If ``ruleset_var`` is not defined by ``code``.
        TypeError: If ``ruleset_var`` does not evaluate to a :class:`RuleSet`.
    """

    exec_globals: dict[str, Any] = {
        "field": field,
        "ruleset": ruleset,
        "when": when,
        "otherwise": otherwise,
        "Else": Else,
        "RuleSet": RuleSet,
        "RuleSetPolicy": RuleSetPolicy,
        "RuleValue": RuleValue,
        "RuleTree": RuleTree,
        "DiscreteDomain": DiscreteDomain,
        "IntervalDomain": IntervalDomain,
    }
    if include_builtins:
        exec_globals.update({"__builtins__": __builtins__})
    else:
        exec_globals.update({"__builtins__": {}})

    if globals_dict is not None:
        exec_globals.update(globals_dict)

    exec_locals = locals_dict if locals_dict is not None else {}

    exec(code, exec_globals, exec_locals)

    namespace = exec_locals
    if ruleset_var not in namespace:
        raise KeyError(f"Ruleset variable {ruleset_var!r} not defined by executed code")

    result = namespace[ruleset_var]
    if not isinstance(result, RuleSet):
        raise TypeError(f"Expected {ruleset_var!r} to contain a RuleSet, got {type(result).__name__}")

    return result
