from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, Union, overload

from unirules.core.conditions import AlwaysTrue, Cond
from unirules.core.rules import RuleItem, RuleSet, RuleSetPolicy, RuleTree, RuleValue, V
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.discrete.field import DiscreteField
from unirules.domains.interval.domain import IntervalDomain
from unirules.domains.interval.field import IntervalField

__all__ = [
    "field",
    "ruleset",
    "when",
    "otherwise",
    "Else",
]


@overload
def field(name: str, domain: DiscreteDomain) -> DiscreteField: ...


@overload
def field(name: str, domain: IntervalDomain) -> IntervalField: ...


def field(name: str, domain: Union[DiscreteDomain, IntervalDomain]) -> Union[DiscreteField, IntervalField]:
    """Create a field object based on the provided domain type.

    Args:
        name (str): The field name.
        domain (Union[DiscreteDomain, IntervalDomain]): Domain describing the
            field.

    Returns:
        Union[DiscreteField, IntervalField]: Field instance matching the
        supplied domain type.

    Raises:
        TypeError: If ``domain`` is neither discrete nor interval.
    """
    if isinstance(domain, DiscreteDomain):
        return DiscreteField(name, domain)
    elif isinstance(domain, IntervalDomain):
        return IntervalField(name, domain)
    else:
        raise TypeError(f"Domain must be DiscreteDomain or IntervalDomain, got {type(domain)}")


@dataclass(frozen=True)
class Else(Generic[V]):
    """A fallback rule for unmatched conditions."""

    result: Union[V, RuleSet[V]]
    name: Optional[str] = "otherwise"


def ruleset(
    *branches: Union[RuleItem[V], Else[V]],
    policy: Union[str, RuleSetPolicy] = RuleSetPolicy.FIRST_WINS,
) -> RuleSet[V]:
    """Create a ruleset from a sequence of rules or a fallback.

    Args:
        branches (Union[RuleItem[V], Else[V]]): Rule branches and optional
            fallback clause.

    Args:
        policy (str | RuleSetPolicy): Evaluation policy for the resulting
            ruleset. Supported values are ``RuleSetPolicy.FIRST_WINS`` and
            ``RuleSetPolicy.PRIORITY`` (or their string equivalents).

    Returns:
        RuleSet[V]: A ruleset that evaluates the provided branches according to
        the selected policy.
    """
    items: list[RuleItem[V]] = []
    fallback: Optional[Else[V]] = None
    for branch in branches:
        if isinstance(branch, Else):
            fallback = branch
            continue
        items.append(branch)
    if fallback is not None:
        if isinstance(fallback.result, RuleSet):
            items.append(RuleTree(AlwaysTrue(), fallback.result, name=fallback.name))
        else:
            items.append(RuleValue(AlwaysTrue(), fallback.result, name=fallback.name))
    return RuleSet(items, policy=policy)


class _Builder(Generic[V]):
    """Helper class to build rules with conditions."""

    def __init__(self, condition: Cond, *, name: Optional[str] = None, priority: int = 0):
        """Initialize the builder with a condition.

        Args:
            condition (Cond): The condition guarding the rule.
            name (Optional[str]): Human-friendly name for the resulting rule.
            priority (int): Priority of the rule within its ruleset.
        """
        self._cond = condition
        self._name = name
        self._priority = priority

    @overload
    def then(self, result: RuleSet[V]) -> RuleTree[V]: ...  # type: ignore[overload-overlap] # right order

    @overload
    def then(self, result: V) -> RuleValue[V]: ...

    def then(self, result: Union[V, RuleSet[V]]) -> RuleItem[V]:
        """Create a rule with the specified result.

        Args:
            result (Union[V, RuleSet[V]]): The value or nested ruleset emitted
                when the condition matches.

        Returns:
            RuleItem[V]: The constructed rule.
        """
        if isinstance(result, RuleSet):
            return RuleTree(self._cond, result, name=self._name, priority=self._priority)
        return RuleValue(self._cond, result, name=self._name, priority=self._priority)


def when(condition: Cond, *, name: Optional[str] = None, priority: int = 0) -> _Builder[V]:
    """Create a rule builder with a condition.

    Args:
        condition (Cond): The condition for the rule.
        name (Optional[str]): Optional name for the resulting rule.
        priority (int): Priority of the rule.

    Returns:
        _Builder[V]: A builder for constructing the rule.
    """
    return _Builder(condition, name=name, priority=priority)


def otherwise(result: Union[V, RuleSet[V]], *, name: Optional[str] = "otherwise") -> Else[V]:
    """Create a fallback rule.

    Args:
        result (Union[V, RuleSet[V]]): The value or ruleset for the fallback.
        name (Optional[str]): Optional name for the fallback branch.

    Returns:
        Else[V]: A fallback rule.
    """
    return Else(result=result, name=name)
