from __future__ import annotations

import pytest

from unirules.core.rules import RuleSet, RuleSetPolicy, RuleTree, RuleValue
from unirules.ruleset_loader import load_ruleset_from_code


def test_load_ruleset_from_code_example() -> None:
    rules_code = """
segment = field("segment", DiscreteDomain({"core", "edge"}))
status = field("status", DiscreteDomain({"VIP", "STD"}))

RULESET = ruleset(
    when(segment == "core", name="core", priority=1).then(
        ruleset(
            when(status == "VIP", name="base", priority=0).then("base"),
            when(status == "VIP", name="override", priority=10).then("override"),
            policy=RuleSetPolicy.PRIORITY,
        )
    ),
    when(segment == "edge", name="edge", priority=5).then("edge"),
    policy=RuleSetPolicy.PRIORITY,
)
"""

    loaded_ruleset = load_ruleset_from_code(rules_code)

    assert isinstance(loaded_ruleset, RuleSet)
    assert loaded_ruleset.policy == RuleSetPolicy.PRIORITY
    assert len(loaded_ruleset.rules) == 2

    first_rule = loaded_ruleset.rules[0]
    assert isinstance(first_rule, RuleTree)
    assert first_rule.name == "core"
    assert first_rule.priority == 1
    assert first_rule.subtree.policy == RuleSetPolicy.PRIORITY
    assert len(first_rule.subtree.rules) == 2

    nested_rule = first_rule.subtree.rules[0]
    assert isinstance(nested_rule, RuleValue)
    assert nested_rule.value == "base"
    assert nested_rule.priority == 0

    second_rule = loaded_ruleset.rules[1]
    assert isinstance(second_rule, RuleValue)
    assert second_rule.value == "edge"
    assert second_rule.priority == 5


def test_load_ruleset_missing_variable() -> None:
    with pytest.raises(KeyError):
        load_ruleset_from_code("x = 1", ruleset_var="missing")


def test_load_ruleset_wrong_type() -> None:
    with pytest.raises(TypeError):
        load_ruleset_from_code("RULESET = 123")
