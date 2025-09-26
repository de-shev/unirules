from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, DefaultDict, Generic, Iterable, Optional

from unirules.core.conditions import AlwaysTrue, And, Cond, CondVisitor, Context, Not, Or
from unirules.core.rules import RuleItem, RuleSet, RuleSetPolicy, RuleTree, RuleValue, V
from unirules.domains.common.conditions import Eq
from unirules.domains.discrete.conditions import In_, NotIn_
from unirules.domains.interval.conditions import Between, Ge, Gt, Le, Lt

__all__ = ["Explanation", "Resolver"]


EvalFn = Callable[[Context], bool]


@dataclass(frozen=True)
class _FieldConstraint:
    """Describe constraints that can be inferred from a condition.

    Attributes:
        field: Name of the context field referenced by the condition.
        values: Frozen set of allowed values for the field, or ``None`` when the
            condition does not restrict the field to a discrete set.
    """

    field: str
    values: Optional[frozenset[object]]


@dataclass(frozen=True)
class _CompiledRuleItem(Generic[V]):
    """Cache data required to evaluate a rule item quickly.

    Attributes:
        rule: The underlying rule definition from the rule set.
        evaluate: Callable that evaluates the rule condition against a context.
        constraints: Tuple of constraints derived from the rule condition.
        subtree: Compiled subtree when the rule value is a nested rule set.
    """

    rule: RuleItem[V]
    evaluate: EvalFn
    constraints: tuple[_FieldConstraint, ...]
    subtree: Optional[_CompiledRuleSet[V]]


@dataclass(frozen=True)
class _CompiledRuleSet(Generic[V]):
    """Compiled representation of a rule set for efficient resolution.

    Attributes:
        ordered: Rules ordered according to the rule set policy.
        indices: Field-value indices pointing to candidate rule positions.
    """

    ordered: tuple[_CompiledRuleItem[V], ...]
    indices: dict[str, dict[object, tuple[int, ...]]]

    def iter_candidates(self, ctx: Context) -> Iterable[_CompiledRuleItem[V]]:
        """Yield rule items that may match a context.

        Args:
            ctx: Resolution context containing field values.

        Yields:
            Compiled rule items ordered by policy with indexed candidates first.
        """

        if not self.indices:
            yield from self.ordered
            return

        seen: set[int] = set()
        for field, value_map in self.indices.items():
            value = ctx.get(field)
            try:
                matches = value_map[value]
            except (KeyError, TypeError):
                continue
            for idx in matches:
                if idx not in seen:
                    seen.add(idx)
                    yield self.ordered[idx]

        for idx, item in enumerate(self.ordered):
            if idx not in seen:
                seen.add(idx)
                yield item

    def resolve(self, ctx: Context) -> V:
        """Resolve the rule set against a context.

        Args:
            ctx: Resolution context containing field values.

        Returns:
            The value of the first matching rule according to the policy.

        Raises:
            LookupError: If no rule matches the provided context.
        """

        for item in self.iter_candidates(ctx):
            if not item.evaluate(ctx):
                continue
            rule = item.rule
            if isinstance(rule, RuleValue):
                return rule.value
            if item.subtree is None:
                raise LookupError("Rule tree missing compiled subtree")
            return item.subtree.resolve(ctx)
        raise LookupError(f"No rule matched for ctx={ctx!r}")


CompileResult = tuple[EvalFn, tuple[_FieldConstraint, ...]]


class CompileVisitor(CondVisitor[CompileResult]):
    """Compile conditions into evaluation callables and constraints."""

    def compile(self, cond: Cond) -> CompileResult:
        return cond.accept(self)

    def _fallback(self, cond: Cond) -> CompileResult:
        def _eval(ctx: Context, *, _cond: Cond = cond) -> bool:
            return _cond.eval(ctx)

        return _eval, tuple()

    def visit_eq(self, cond: Eq) -> CompileResult:
        field = cond.field.name
        value = cond.value

        def _eval(ctx: Context, *, _field: str = field, _value: object = value) -> bool:
            return ctx.get(_field) == _value

        constraint: tuple[_FieldConstraint, ...]
        try:
            constraint = (_FieldConstraint(field=field, values=frozenset([value])),)
        except TypeError:
            constraint = ()
        return _eval, constraint

    def visit_in(self, cond: In_) -> CompileResult:
        field = cond.field.name
        items = cond.items

        def _eval(
            ctx: Context,
            *,
            _field: str = field,
            _items: frozenset[object] = items,
        ) -> bool:
            return ctx.get(_field) in _items

        constraint = (_FieldConstraint(field=field, values=frozenset(items)),)
        return _eval, constraint

    def visit_notin(self, cond: NotIn_) -> CompileResult:  # pragma: no cover - not used for compilation yet
        return self._fallback(cond)

    def visit_between(self, cond: Between) -> CompileResult:
        field = cond.field.name
        closed = cond.closed
        try:
            lo = float(cond.lo)
            hi = float(cond.hi)
        except (TypeError, ValueError):
            return self._fallback(cond)

        def _eval(
            ctx: Context,
            *,
            _field: str = field,
            _lo: float = lo,
            _hi: float = hi,
            _closed: str = closed,
        ) -> bool:
            raw = ctx.get(_field)
            try:
                v = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False
            left = v > _lo if _closed in ("right", "none") else v >= _lo
            right = v < _hi if _closed in ("left", "none") else v <= _hi
            return left and right

        return _eval, tuple()

    def visit_gt(self, cond: Gt) -> CompileResult:
        field = cond.field.name
        try:
            value = float(cond.value)
        except (TypeError, ValueError):
            return self._fallback(cond)

        def _eval(ctx: Context, *, _field: str = field, _value: float = value) -> bool:
            raw = ctx.get(_field)
            try:
                v = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False
            return v > _value

        return _eval, tuple()

    def visit_ge(self, cond: Ge) -> CompileResult:
        field = cond.field.name
        try:
            value = float(cond.value)
        except (TypeError, ValueError):
            return self._fallback(cond)

        def _eval(ctx: Context, *, _field: str = field, _value: float = value) -> bool:
            raw = ctx.get(_field)
            try:
                v = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False
            return v >= _value

        return _eval, tuple()

    def visit_lt(self, cond: Lt) -> CompileResult:
        field = cond.field.name
        try:
            value = float(cond.value)
        except (TypeError, ValueError):
            return self._fallback(cond)

        def _eval(ctx: Context, *, _field: str = field, _value: float = value) -> bool:
            raw = ctx.get(_field)
            try:
                v = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False
            return v < _value

        return _eval, tuple()

    def visit_le(self, cond: Le) -> CompileResult:
        field = cond.field.name
        try:
            value = float(cond.value)
        except (TypeError, ValueError):
            return self._fallback(cond)

        def _eval(ctx: Context, *, _field: str = field, _value: float = value) -> bool:
            raw = ctx.get(_field)
            try:
                v = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False
            return v <= _value

        return _eval, tuple()

    def visit_and(self, cond: And) -> CompileResult:
        left_eval, left_constraints = self.compile(cond.a)
        right_eval, right_constraints = self.compile(cond.b)

        def _eval(ctx: Context, *, _l: EvalFn = left_eval, _r: EvalFn = right_eval) -> bool:
            return _l(ctx) and _r(ctx)

        return _eval, left_constraints + right_constraints

    def visit_or(self, cond: Or) -> CompileResult:
        left_eval, left_constraints = self.compile(cond.a)
        right_eval, right_constraints = self.compile(cond.b)

        def _eval(ctx: Context, *, _l: EvalFn = left_eval, _r: EvalFn = right_eval) -> bool:
            return _l(ctx) or _r(ctx)

        return _eval, left_constraints + right_constraints

    def visit_not(self, cond: Not) -> CompileResult:
        inner_eval, _ = self.compile(cond.a)

        def _eval(ctx: Context, *, _inner: EvalFn = inner_eval) -> bool:
            return not _inner(ctx)

        return _eval, tuple()

    def visit_always_true(self, cond: AlwaysTrue) -> CompileResult:  # noqa: ARG002 - signature required
        def _eval(ctx: Context) -> bool:  # noqa: ARG001 - ctx required by signature
            return True

        return _eval, tuple()


def _build_indices(items: list[_CompiledRuleItem[V]]) -> dict[str, dict[object, tuple[int, ...]]]:
    """Build field-value indices for compiled rule items.

    Args:
        items: Compiled rule items ordered by policy.

    Returns:
        Mapping from field name to value-to-rule-index tuples.
    """

    buckets: DefaultDict[str, DefaultDict[object, list[int]]] = defaultdict(lambda: defaultdict(list))
    for idx, item in enumerate(items):
        for constraint in item.constraints:
            values = constraint.values
            if not values:
                continue
            for value in values:
                try:
                    bucket = buckets[constraint.field][value]
                except TypeError:
                    continue
                bucket.append(idx)

    frozen: dict[str, dict[object, tuple[int, ...]]] = {}
    for field, value_map in buckets.items():
        frozen[field] = {value: tuple(indices) for value, indices in value_map.items() if indices}
    return frozen


def _compile_ruleset(ruleset: RuleSet[V]) -> _CompiledRuleSet[V]:
    """Compile a rule set into the optimized representation used by resolvers.

    Args:
        ruleset: Rule set definition to compile.

    Returns:
        Compiled rule set with ordered items and field indices.

    Raises:
        ValueError: If the rule set policy is not supported.
    """

    enumerated = list(enumerate(ruleset.rules))
    policy = ruleset.policy
    if policy is RuleSetPolicy.PRIORITY:
        enumerated.sort(key=lambda pair: (-pair[1].priority, pair[0]))
    elif policy is not RuleSetPolicy.FIRST_WINS:
        raise ValueError(f"Unsupported ruleset policy: {policy!r}")

    compiled_items: list[_CompiledRuleItem[V]] = []
    visitor = CompileVisitor()
    for _, rule in enumerated:
        eval_fn, constraints = visitor.compile(rule.condition)
        subtree = None
        if isinstance(rule, RuleTree):
            subtree = _compile_ruleset(rule.subtree)
        compiled_items.append(
            _CompiledRuleItem(
                rule=rule,
                evaluate=eval_fn,
                constraints=constraints,
                subtree=subtree,
            )
        )

    return _CompiledRuleSet(
        ordered=tuple(compiled_items),
        indices=_build_indices(compiled_items),
    )


@dataclass(frozen=True)
class Explanation(Generic[V]):
    """Explanation of how a resolver matched a context."""

    matched_rule: Optional[str]
    path: list[str]
    tested: list[str]
    result: Optional[V]


class Resolver(Generic[V]):
    """Resolve values from rule sets using a compiled representation."""

    def __init__(self, ruleset: RuleSet[V]):
        """Create a resolver.

        Args:
            ruleset: Rule set definition to use for resolution.
        """

        self.ruleset = ruleset
        self._compiled = _compile_ruleset(ruleset)

    def resolve(self, ctx: Context) -> V:
        """Resolve the rule set for the provided context.

        Args:
            ctx: Resolution context containing field values.

        Returns:
            The value produced by the first matching rule.
        """

        return self._compiled.resolve(ctx)

    def explain(self, ctx: Context) -> Explanation[V]:
        """Explain how the rule set resolves for a context.

        Args:
            ctx: Resolution context containing field values.

        Returns:
            Explanation describing the evaluation path and result.
        """

        tested: list[str] = []
        for item in self._compiled.iter_candidates(ctx):
            label = getattr(item.rule, "name", None) or "<rule>"
            ok = item.evaluate(ctx)
            tested.append(f"{label}: {'✓' if ok else '×'}")
            if not ok:
                continue

            path = [label]
            current = item
            result: Optional[V] = None
            while True:
                rule = current.rule
                if isinstance(rule, RuleValue):
                    result = rule.value
                    break
                if current.subtree is None:
                    break
                found = False
                for child in current.subtree.iter_candidates(ctx):
                    if child.evaluate(ctx):
                        child_label = getattr(child.rule, "name", None) or "<rule>"
                        path.append(child_label)
                        current = child
                        found = True
                        break
                if not found:
                    break

            return Explanation(
                matched_rule=label,
                path=path,
                tested=tested,
                result=result,
            )

        return Explanation(matched_rule=None, path=[], tested=tested, result=None)
