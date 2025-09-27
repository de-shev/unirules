# unirules

unirules is a Python library for building declarative rule sets with a friendly DSL over discrete and interval domains, then turning them into runtime resolvers and analyzers that fit into your applications.

## Installation

```shell
pip install unirules
```

## Features

- **Resolver with explanations.** Rule sets compile down to a resolver that respects first-wins and priority policies, evaluates contexts, and reports the matched path alongside every tested rule.
- **Symbolic analyzer.** Inspect coverage across discrete and interval domains, with per-rule value sets and uncovered segments that honor nested structures and optional context filters.
- **Expressive DSL.** Declare fields with equality, membership, and numeric operators, then combine `when`, `ruleset`, and `otherwise` clauses—with optional names and priorities—to build nested decision trees.
- **Dynamic loading.** Execute DSL snippets at runtime with `load_ruleset_from_code`, which preloads the necessary helpers so rule sets can live in configuration files or databases.

## Usage

### Build and resolve a ruleset

Use the DSL to declare fields, nest rulesets, resolve a context, and inspect the resolver’s explanation of what matched.

```python
from unirules import DiscreteDomain, IntervalDomain, field, otherwise, ruleset, when

credit_score = field("credit_score", IntervalDomain(300, 850))
income_level = field("income_level", DiscreteDomain({"LOW", "HIGH"}))

loan_rules = ruleset(
    when(income_level == "HIGH", name="High income").then(
        ruleset(
            when(credit_score.between(700, 850), name="Top tier").then(
                {"decision": "APPROVE", "rate": 3.5}
            ),
            otherwise({"decision": "REVIEW", "rate": 7.0}, name="High fallback"),
        )
    ),
    when(credit_score < 500, name="Low credit reject").then({"decision": "REJECT", "rate": None}),
    otherwise({"decision": "REVIEW", "rate": None}, name="Default review"),
)

resolver = loan_rules.to_resolver()

decision = resolver.resolve({"income_level": "HIGH", "credit_score": 720})
explanation = resolver.explain({"income_level": "HIGH", "credit_score": 720})
print(decision)          # {'decision': 'APPROVE', 'rate': 3.5}
print(explanation.path)  # ['High income', 'Top tier']
```

### Analyze coverage

Analyze coverage for a field while applying optional context filters; the analyzer reports covered values per rule along with any remaining uncovered portion of the domain.

```python
analyzer = loan_rules.to_analyzer()

analysis = analyzer.analyze(target=income_level, ctx={"credit_score": 720})
print(analysis.covered_values())   # {'LOW', 'HIGH'}
print(analysis.uncovered_values()) # set()
print(analysis.by_rule)            # [((0, 0), {'HIGH'}, {...}), ((2,), {'LOW'}, {...})]
```

### Load rulesets from code

Load a ruleset from a code string—complete with DSL helpers already in scope—and use it like any other ruleset.

```python
from unirules import load_ruleset_from_code

rules_source = """
segment = field("segment", DiscreteDomain({"core", "edge"}))

RULESET = ruleset(
    when(segment == "core", name="Core branch", priority=5).then("CORE"),
    otherwise("EDGE", name="Fallback"),
    policy="priority",
)
"""

loaded_rules = load_ruleset_from_code(rules_source)
print(loaded_rules.to_resolver().resolve({"segment": "edge"}))  # EDGE
```