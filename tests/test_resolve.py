from collections.abc import Mapping
from typing import Any

import pytest

from unirules import RuleSetPolicy, field, ruleset, when
from unirules.domains.discrete.domain import DiscreteDomain

from .credit_scoring import LoanDecision, credit_score


@pytest.mark.parametrize(
    ("ctx", "expected"),
    [
        pytest.param(
            {"income_level": "HIGH", "credit_score": 750, "loan_purpose": "AUTO"},
            LoanDecision(decision="APPROVE", rate=3.5),
            id="high-income-top-tier",
        ),
        pytest.param(
            {
                "income_level": "HIGH",
                "credit_score": 650,
                "loan_purpose": "PERSONAL",
            },
            LoanDecision(decision="APPROVE", rate=5.0),
            id="high-income-standard-tier",
        ),
        pytest.param(
            {
                "income_level": "HIGH",
                "credit_score": 400,
                "loan_purpose": "MORTGAGE",
            },
            LoanDecision(decision="REVIEW", rate=7.0),
            id="high-income-fallback",
        ),
        pytest.param(
            {
                "income_level": "MEDIUM",
                "loan_purpose": "MORTGAGE",
                "credit_score": 600,
            },
            LoanDecision(decision="APPROVE", rate=4.5),
            id="medium-mortgage-approval",
        ),
        pytest.param(
            {
                "income_level": "MEDIUM",
                "loan_purpose": "MORTGAGE",
                "credit_score": 450,
            },
            LoanDecision(decision="APPROVE", rate=4.5),
            id="medium-mortgage-priority",
        ),
        pytest.param(
            {
                "credit_score": 450,
                "income_level": "LOW",
                "loan_purpose": "AUTO",
            },
            LoanDecision(decision="REJECT", rate=None),
            id="low-credit-reject",
        ),
        pytest.param(
            {
                "income_level": "LOW",
                "loan_purpose": "AUTO",
                "credit_score": 550,
            },
            LoanDecision(decision="REVIEW", rate=None),
            id="default-review",
        ),
        pytest.param(
            {"income_level": "LOW"},
            LoanDecision(decision="REVIEW", rate=None),
            id="missing-fields",
        ),
        pytest.param(
            {
                "income_level": "HIGH",
                "credit_score": 850,
                "loan_purpose": "AUTO",
            },
            LoanDecision(decision="APPROVE", rate=3.5),
            id="high-income-upper-boundary",
        ),
        pytest.param(
            {
                "income_level": "HIGH",
                "loan_purpose": "PERSONAL",
            },
            LoanDecision(decision="REVIEW", rate=7.0),
            id="high-income-missing-score",
        ),
    ],
)
def test_credit_scoring_resolver_returns_expected(
    credit_scoring_resolver, ctx: Mapping[str, Any], expected: LoanDecision
) -> None:
    """Verify that the resolver returns the correct decision for diverse contexts."""

    assert credit_scoring_resolver.resolve(ctx) == expected


def test_resolve_no_match_raises_lookuperror() -> None:
    """Test that LookupError is raised when no rule matches the context."""

    temp_resolver = ruleset(
        when(credit_score.between(700, 850)).then({"decision": "APPROVE"}),
    ).to_resolver()
    ctx: Mapping[str, Any] = {"credit_score": 600}
    with pytest.raises(LookupError, match="No rule matched"):
        temp_resolver.resolve(ctx)


def test_resolver_rejects_invalid_discrete_context(credit_scoring_resolver) -> None:
    """Invalid discrete context values raise a ValueError."""

    with pytest.raises(ValueError, match="income_level"):
        credit_scoring_resolver.resolve({"income_level": "ULTRA_HIGH"})


def test_resolver_rejects_invalid_interval_context(credit_scoring_resolver) -> None:
    """Non-numeric interval context values raise a ValueError."""

    with pytest.raises(ValueError, match="credit_score"):
        credit_scoring_resolver.resolve({"credit_score": "not-a-number"})


def test_priority_policy_prefers_highest_priority_rule() -> None:
    """Resolver honours rule priority over declaration order when requested."""

    status = field("status", DiscreteDomain({"VIP", "STD"}))
    resolver = ruleset(
        when(status == "VIP", name="low", priority=0).then("low"),
        when(status == "VIP", name="high", priority=10).then("high"),
        policy="priority",
    ).to_resolver()

    assert resolver.resolve({"status": "VIP"}) == "high"


def test_priority_policy_preserves_order_for_equal_priority() -> None:
    """Rules with equal priority fall back to declaration order."""

    status = field("status", DiscreteDomain({"VIP"}))
    resolver = ruleset(
        when(status == "VIP", name="first", priority=5).then("first"),
        when(status == "VIP", name="second", priority=5).then("second"),
        policy="priority",
    ).to_resolver()

    assert resolver.resolve({"status": "VIP"}) == "first"


def test_priority_policy_nested_ruleset_uses_priority() -> None:
    """Nested rulesets configured with priority respect inner priorities."""

    segment = field("segment", DiscreteDomain({"core", "edge"}))
    status = field("status", DiscreteDomain({"VIP", "STD"}))

    resolver = ruleset(
        when(segment == "core", name="core", priority=1).then(
            ruleset(
                when(status == "VIP", name="base", priority=0).then("base"),
                when(status == "VIP", name="override", priority=10).then("override"),
                policy=RuleSetPolicy.PRIORITY,
            )
        ),
        when(segment == "edge", name="edge", priority=5).then("edge"),
        policy=RuleSetPolicy.PRIORITY,
    ).to_resolver()

    assert resolver.resolve({"segment": "core", "status": "VIP"}) == "override"


def test_ruleset_rejects_unknown_policy() -> None:
    """Invalid policy values raise a ValueError during ruleset construction."""

    status = field("status", DiscreteDomain({"VIP"}))

    with pytest.raises(ValueError, match="Unsupported ruleset policy"):
        ruleset(when(status == "VIP").then("vip"), policy="unknown")
