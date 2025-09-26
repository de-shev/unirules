"""
Rule classes and builders for the rule evaluation system.

This module contains rule definitions, the ruleset execution engine,
and builder patterns for creating rules with fluent syntax.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, Union

from typing_extensions import TypeAlias

from unirules.core.conditions import Cond

if TYPE_CHECKING:
    from unirules.engines.analyzer import Analyzer
    from unirules.engines.resolver import Resolver

V = TypeVar("V")

__all__ = ["RuleValue", "RuleTree", "RuleItem", "RuleSet", "RuleSetPolicy", "V"]


class RuleSetPolicy(str, Enum):
    """Enumeration of supported evaluation strategies for a :class:`RuleSet`."""

    FIRST_WINS = "first_wins"
    PRIORITY = "priority"


@dataclass(frozen=True)
class RuleValue(Generic[V]):
    """A rule that assigns a value when its condition is met."""

    condition: Cond
    value: V
    name: Optional[str] = None
    priority: int = 0


@dataclass(frozen=True)
class RuleTree(Generic[V]):
    """A rule that branches to a subtree when its condition is met."""

    condition: Cond
    subtree: "RuleSet[V]"
    name: Optional[str] = None
    priority: int = 0


RuleItem: TypeAlias = Union[RuleValue[V], RuleTree[V]]


class RuleSet(Generic[V]):
    """A collection of rules evaluated in order."""

    def __init__(
        self,
        rules: Sequence[RuleItem[V]],
        *,
        policy: Union[str, RuleSetPolicy] = RuleSetPolicy.FIRST_WINS,
    ):
        """Initialize the ruleset.

        Args:
            rules (Sequence[RuleItem[V]]): Ordered sequence of rule items to
                evaluate.
            policy (str | RuleSetPolicy): Evaluation policy controlling how
                rules are traversed during resolution and analysis.
        """
        self.rules: list[RuleItem[V]] = list(rules)
        if isinstance(policy, RuleSetPolicy):
            self.policy = policy
        elif isinstance(policy, str):
            try:
                self.policy = RuleSetPolicy(policy)
            except ValueError as exc:
                raise ValueError(f"Unsupported ruleset policy: {policy!r}") from exc
        else:
            raise TypeError(
                f"Policy must be specified as a string or RuleSetPolicy, got {type(policy).__name__}",
            )

    def to_resolver(self) -> "Resolver[V]":
        from unirules.engines.resolver import Resolver  # noqa: PLC0415

        return Resolver(ruleset=self)

    def to_analyzer(self) -> "Analyzer[V]":
        from unirules.engines.analyzer import Analyzer  # noqa: PLC0415

        return Analyzer(ruleset=self)
