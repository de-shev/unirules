"""
Symbolic analysis functionality for rulesets.

This module provides inverse analysis (symbolic projection) capabilities
for understanding what values of a target field are covered by rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Mapping, Optional, Union, cast, overload

from typing_extensions import TypeAlias

from unirules.core.conditions import AlwaysTrue, And, Cond, CondVisitor, Context, Not, Or
from unirules.core.domains import ValueSet
from unirules.core.rules import RuleItem, RuleSet, RuleSetPolicy, RuleTree, RuleValue, V
from unirules.domains.common.conditions import Eq
from unirules.domains.discrete.conditions import In_, NotIn_
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.discrete.field import DiscreteField
from unirules.domains.discrete.field_ref import DiscreteFieldRef
from unirules.domains.discrete.values import DiscreteSet
from unirules.domains.interval.conditions import Between, Ge, Gt, Le, Lt
from unirules.domains.interval.domain import IntervalDomain
from unirules.domains.interval.field import IntervalField
from unirules.domains.interval.field_ref import IntervalFieldRef
from unirules.domains.interval.values import Interval, IntervalSet

__all__ = [
    "TOP",
    "BOT",
    "ProjectionResult",
    "ProjectionVisitor",
    "project",
    "AnalyzeResult",
    "DiscreteAnalyzeResult",
    "IntervalAnalyzeResult",
    "Analyzer",
]


class _Top:
    __slots__ = ()


class _Bot:
    __slots__ = ()


TOP = _Top()
BOT = _Bot()

ProjectionResult: TypeAlias = Union[ValueSet, _Top, _Bot]


def _coerce_float(value: Optional[object]) -> Optional[float]:
    """Best-effort conversion of a context value to ``float`` for comparisons."""

    if value is None:
        return None
    try:
        return float(cast(Any, value))
    except (TypeError, ValueError):
        return None


class ProjectionVisitor(CondVisitor[ProjectionResult]):
    def __init__(
        self,
        *,
        target: str,
        target_domain: Union[DiscreteDomain, IntervalDomain],
        ctx: Optional[Context] = None,
    ) -> None:
        self.target = target
        self.target_domain = target_domain
        self.ctx = ctx

    def _ctx_get(self, name: str) -> tuple[bool, Optional[object]]:
        if self.ctx is None:
            return (False, None)
        return (name in self.ctx, self.ctx.get(name))

    def visit_eq(self, cond: Eq) -> ProjectionResult:
        if cond.field.name == self.target:
            return DiscreteSet([cond.value])
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        return TOP if v == cond.value else BOT

    def visit_in(self, cond: In_) -> ProjectionResult:
        if cond.field.name == self.target:
            return DiscreteSet(cond.items)
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        return TOP if v in cond.items else BOT

    def visit_notin(self, cond: NotIn_) -> ProjectionResult:
        if cond.field.name == self.target:
            universe = cast(DiscreteSet, self.target_domain.get_universe())
            return universe.diff(DiscreteSet(cond.items))
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        return BOT if v in cond.items else TOP

    def visit_between(self, cond: Between) -> ProjectionResult:
        if cond.field.name == self.target:
            lo, hi, closed = float(cond.lo), float(cond.hi), cond.closed
            return IntervalSet([(lo, hi, closed)])
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        val = _coerce_float(v)
        if val is None:
            return BOT
        lo = float(cond.lo)
        hi = float(cond.hi)
        left = val > lo if cond.closed in ("right", "none") else val >= lo
        right = val < hi if cond.closed in ("left", "none") else val <= hi
        return TOP if (left and right) else BOT

    def visit_gt(self, cond: Gt) -> ProjectionResult:  # noqa: PLR0911
        threshold = float(cond.value)
        if cond.field.name == self.target:
            if isinstance(self.target_domain, IntervalDomain):
                universe = cast(IntervalSet, self.target_domain.get_universe())
                if not universe.segs:
                    return BOT
                lo, hi, _ = universe.segs[0]
                if threshold >= hi:
                    return BOT
                elif threshold < lo:
                    return universe
                else:
                    return IntervalSet([(threshold, hi, "right")])
            else:
                domain = cast(DiscreteDomain, self.target_domain)
                return DiscreteSet([v for v in domain.vals if v > threshold])
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        ctx_val = _coerce_float(v)
        if ctx_val is None:
            return BOT
        return TOP if ctx_val > threshold else BOT

    def visit_ge(self, cond: Ge) -> ProjectionResult:  # noqa: PLR0911
        threshold = float(cond.value)
        if cond.field.name == self.target:
            if isinstance(self.target_domain, IntervalDomain):
                universe = cast(IntervalSet, self.target_domain.get_universe())
                if not universe.segs:
                    return BOT
                lo, hi, _ = universe.segs[0]
                if threshold > hi:
                    return BOT
                elif threshold <= lo:
                    return universe
                else:
                    return IntervalSet([(threshold, hi, "both")])
            else:
                domain = cast(DiscreteDomain, self.target_domain)
                return DiscreteSet([v for v in domain.vals if v >= threshold])
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        ctx_val = _coerce_float(v)
        if ctx_val is None:
            return BOT
        return TOP if ctx_val >= threshold else BOT

    def visit_lt(self, cond: Lt) -> ProjectionResult:  # noqa: PLR0911
        threshold = float(cond.value)
        if cond.field.name == self.target:
            if isinstance(self.target_domain, IntervalDomain):
                universe = cast(IntervalSet, self.target_domain.get_universe())
                if not universe.segs:
                    return BOT
                lo, hi, _ = universe.segs[0]
                if threshold <= lo:
                    return BOT
                elif threshold > hi:
                    return universe
                else:
                    return IntervalSet([(lo, threshold, "left")])
            else:
                domain = cast(DiscreteDomain, self.target_domain)
                return DiscreteSet([v for v in domain.vals if v < threshold])
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        ctx_val = _coerce_float(v)
        if ctx_val is None:
            return BOT
        return TOP if ctx_val < threshold else BOT

    def visit_le(self, cond: Le) -> ProjectionResult:  # noqa: PLR0911
        threshold = float(cond.value)
        if cond.field.name == self.target:
            if isinstance(self.target_domain, IntervalDomain):
                universe = cast(IntervalSet, self.target_domain.get_universe())
                if not universe.segs:
                    return BOT
                lo, hi, _ = universe.segs[0]
                if threshold < lo:
                    return BOT
                elif threshold >= hi:
                    return universe
                else:
                    return IntervalSet([(lo, threshold, "both")])
            else:
                domain = cast(DiscreteDomain, self.target_domain)
                return DiscreteSet([v for v in domain.vals if v <= threshold])
        known, v = self._ctx_get(cond.field.name)
        if not known:
            return TOP
        ctx_val = _coerce_float(v)
        if ctx_val is None:
            return BOT
        return TOP if ctx_val <= threshold else BOT

    def visit_and(self, cond: And) -> ProjectionResult:
        a = cond.a.accept(self)
        b = cond.b.accept(self)
        if a is BOT or b is BOT:
            return BOT
        if a is TOP:
            return b
        if b is TOP:
            return a
        assert isinstance(a, ValueSet)
        assert isinstance(b, ValueSet)
        return a.inter(b)

    def visit_or(self, cond: Or) -> ProjectionResult:
        a = cond.a.accept(self)
        b = cond.b.accept(self)
        if a is TOP or b is TOP:
            return TOP
        if a is BOT:
            return b
        if b is BOT:
            return a
        assert isinstance(a, ValueSet)
        assert isinstance(b, ValueSet)
        return a.union(b)

    def visit_not(self, cond: Not) -> ProjectionResult:
        p = cond.a.accept(self)
        if p is TOP:
            return BOT
        if p is BOT:
            return TOP
        universe = self.target_domain.get_universe()
        assert isinstance(p, ValueSet)
        return p.complement(universe)

    def visit_always_true(self, cond: AlwaysTrue) -> ProjectionResult:
        return TOP


def project(
    cond: Cond,
    *,
    target: str,
    target_domain: Union[DiscreteDomain, IntervalDomain],
    ctx: Optional[Context] = None,
) -> ProjectionResult:
    """Project a condition onto a target field.

    This function is context-aware: conditions on non-target fields are
    evaluated against the provided ``ctx`` (if any). If such a condition
    contradicts ``ctx``, the projection yields :data:`BOT`; if it is satisfied
    by ``ctx``, it contributes :data:`TOP`; otherwise (unknown), it yields
    :data:`TOP` as well since it does not restrict the target directly.

    Args:
        cond (Cond): The condition to project.
        target (str): The target field name.
        target_domain (Union[DiscreteDomain, IntervalDomain]): The domain of
            the target field.
        ctx (Optional[Context]): Current context for non-target field
            evaluation.

    Returns:
        ProjectionResult: The projected domain or :data:`TOP`/:data:`BOT`.
    """
    visitor = ProjectionVisitor(target=target, target_domain=target_domain, ctx=ctx)
    return cond.accept(visitor)


@dataclass
class AnalyzeResult(Generic[V]):
    """Result of symbolic analysis for a ruleset.

    Provides convenience methods to extract covered and uncovered values for
    discrete domains. For non-discrete (interval) domains these helpers return
    ``None`` because enumerating concrete values is not meaningful.
    """

    by_rule: list[tuple[tuple[int, ...], ValueSet, V]]
    uncovered: ValueSet


@dataclass
class DiscreteAnalyzeResult(AnalyzeResult[V]):
    """Symbolic analysis for discrete target domains.

    Provides concrete value sets for covered and uncovered values.
    """

    def covered_values(self) -> set[object]:
        """Return the set of covered discrete values.

        Returns:
            set[object]: Concrete values covered by the analyzed rules.
        """

        covered: set[object] = set()
        for _, dom, _ in self.by_rule:
            if isinstance(dom, DiscreteSet):
                covered.update(dom.vals)
        return covered

    def uncovered_values(self) -> set[object]:
        """Return the set of uncovered discrete values.

        Returns:
            set[object]: Concrete values not covered by the analyzed rules.
        """

        assert isinstance(self.uncovered, DiscreteSet)
        return set(self.uncovered.vals)


@dataclass
class IntervalAnalyzeResult(AnalyzeResult[V]):
    """Symbolic analysis for interval target domains.

    Helpers return concrete lists of segments ``(lo, hi, closed)`` for covered
    and uncovered ranges.
    """

    def covered_values(self) -> list[Interval]:
        """Return covered interval segments.

        Returns:
            list[Interval]: Normalized list of covered intervals.
        """

        # Aggregate and normalize segments across rules
        acc = IntervalSet([])
        for _, dom, _ in self.by_rule:
            if isinstance(dom, IntervalSet):
                acc = acc.union(dom)
        return list(acc.segs)

    def uncovered_values(self) -> list[Interval]:
        """Return uncovered interval segments.

        Returns:
            list[Interval]: Normalized list of uncovered intervals.
        """

        assert isinstance(self.uncovered, IntervalSet)
        return list(self.uncovered.segs)


def _recursive_collect_domains(
    ruleset: RuleSet[V],
) -> dict[str, Union[DiscreteDomain, IntervalDomain]]:
    """Collect domains from a ruleset and its subtrees.

    Args:
        ruleset (RuleSet[V]): The ruleset from which to collect field domains.

    Returns:
        dict[str, Union[DiscreteDomain, IntervalDomain]]: Mapping of field
            names to their associated domains.
    """
    domains: dict[str, Union[DiscreteDomain, IntervalDomain]] = {}

    def _add_domain(name: str, domain: Union[DiscreteDomain, IntervalDomain]):
        if name in domains and domains[name] is not domain:
            raise ValueError(f"Inconsistent domain for field '{name}'")
        domains[name] = domain

    def _collect_from_cond(cond: Cond):
        if isinstance(cond, (And, Or)):
            _collect_from_cond(cond.a)
            _collect_from_cond(cond.b)
        elif isinstance(cond, Not):
            _collect_from_cond(cond.a)
        elif hasattr(cond, "field"):
            field = cond.field
            _add_domain(field.name, field.domain)

    def _process_ruleset(rs: RuleSet[V]):
        for item in rs.rules:
            _collect_from_cond(item.condition)
            if isinstance(item, RuleTree):
                _process_ruleset(item.subtree)

    _process_ruleset(ruleset)
    return domains


def _ordered_rule_items(ruleset: RuleSet[V]) -> list[tuple[int, RuleItem[V]]]:
    enumerated = list(enumerate(ruleset.rules))
    policy = ruleset.policy
    if policy is RuleSetPolicy.FIRST_WINS:
        return enumerated
    if policy is RuleSetPolicy.PRIORITY:
        return sorted(enumerated, key=lambda pair: (-pair[1].priority, pair[0]))
    raise ValueError(f"Unsupported ruleset policy: {policy!r}")


class Analyzer(Generic[V]):
    def __init__(self, ruleset: RuleSet[V]):
        self.ruleset = ruleset
        self.domains = _recursive_collect_domains(ruleset=ruleset)

    @overload
    def analyze(
        self,
        *,
        target: DiscreteField,
        ctx: Optional[Context] = None,
    ) -> DiscreteAnalyzeResult[V]: ...

    @overload
    def analyze(
        self,
        *,
        target: IntervalField,
        ctx: Optional[Context] = None,
    ) -> IntervalAnalyzeResult[V]: ...

    def analyze(
        self,
        *,
        target: Union[DiscreteField, IntervalField],
        ctx: Optional[Context] = None,
    ) -> Union[DiscreteAnalyzeResult[V], IntervalAnalyzeResult[V]]:
        """Perform symbolic analysis on a ruleset for a target field.

        This implementation respects nested :class:`RuleSet` (:class:`RuleTree`)
        structure and the ``"first_wins"`` / ``"priority"`` policies by traversing
        rules according to the configured evaluation strategy and
        accumulating coverage from leaf-value rules only. Context (``ctx``)
        constraints are converted to an additional filter condition and applied
        throughout the traversal.

        Args:
            target (Union[DiscreteField, IntervalField]): The target field for
                analysis.
            ctx (Optional[Context]): Additional context to constrain the
                analysis (fields other than the target field are converted to
                equality conditions and combined with ``AND``).

        Returns:
            Union[DiscreteAnalyzeResult[V], IntervalAnalyzeResult[V]]: The
            result of the symbolic analysis.
        """

        # Target comes as a Field; use it directly without extra checks
        target_name = target.name
        target_domain = target.domain
        result_class = DiscreteAnalyzeResult if isinstance(target_domain, DiscreteDomain) else IntervalAnalyzeResult

        # Use precomputed domains from the ruleset for ctx filter (faster)
        domains: Mapping[str, Union[DiscreteDomain, IntervalDomain]] = self.domains

        universe = target_domain.get_universe()

        # Track the remaining uncovered portion of the universe.
        # Working with the shrinking uncovered domain is cheaper than
        # growing a covered accumulator because set/interval operations
        # operate on progressively smaller inputs.
        remaining: ValueSet = universe

        out: list[tuple[tuple[int, ...], ValueSet, V]] = []

        def _ctx_filter(
            target_field: str,
            domains: Mapping[str, Union[DiscreteDomain, IntervalDomain]],
            ctx: Mapping[str, object],
        ) -> Cond:
            """Create a filter condition from the context.

            Args:
                target_field (str): The target field to exclude from the
                    generated filter.
                domains (Mapping[str, DiscreteDomain | IntervalDomain]): Known
                    domains keyed by field name.
                ctx (Mapping[str, object]): Context values to convert into
                    equality conditions.

            Returns:
                Cond: The combined condition derived from the provided context.
            """
            if not ctx:
                return AlwaysTrue()
            c: Optional[Cond] = None
            for k, v in ctx.items():
                if k == target_field:
                    continue
                fr_domain = domains.get(k)
                if isinstance(fr_domain, DiscreteDomain):
                    atom = Eq(DiscreteFieldRef(k, fr_domain), v)
                elif isinstance(fr_domain, IntervalDomain):
                    atom = Eq(IntervalFieldRef(k, fr_domain), v)
                else:
                    # Skip ctx keys without known domain in analysis
                    continue
                c = atom if c is None else And(c, atom)
            return c or AlwaysTrue()

        gfilter = _ctx_filter(target_name, domains, ctx or {})

        def _and(a: Cond, b: Cond) -> Cond:
            return a if isinstance(b, AlwaysTrue) else (b if isinstance(a, AlwaysTrue) else And(a, b))

        def process_item(item: RuleItem[V], prefix: Cond, index_path: tuple[int, ...]):
            nonlocal remaining
            if remaining.is_empty():
                return
            if isinstance(item, RuleValue):
                cond = _and(prefix, item.condition)
                dom = project(
                    cond,
                    target=target_name,
                    target_domain=target_domain,
                    ctx=ctx,
                )
                if dom is BOT:
                    return
                if dom is TOP:
                    dom = universe
                assert isinstance(dom, ValueSet)
                dom_clean = dom.inter(remaining)
                if not dom_clean.is_empty():
                    out.append((index_path, dom_clean, item.value))
                    remaining = remaining.diff(dom_clean)
                return
            # RuleTree: dive into subtree with accumulated condition
            assert isinstance(item, RuleTree)
            new_prefix = _and(prefix, item.condition)
            for sub_index, sub_item in _ordered_rule_items(item.subtree):
                if remaining.is_empty():
                    break
                process_item(sub_item, new_prefix, (*index_path, sub_index))

        # Traverse rules depth-first, preserving the original index path for outputs
        for i, it in _ordered_rule_items(self.ruleset):
            if remaining.is_empty():
                break
            process_item(it, gfilter, (i,))

        return result_class(by_rule=out, uncovered=remaining)
