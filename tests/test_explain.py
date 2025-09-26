from collections.abc import Mapping
from typing import Any

import pytest

from unirules import ruleset, when

from .credit_scoring import LoanDecision, build_credit_scoring_ruleset, income_level


@pytest.fixture
def credit_scoring_ruleset():
    """Expose the raw ruleset for tests that need structural access."""

    return build_credit_scoring_ruleset()


def test_explain_nested_match(credit_scoring_resolver) -> None:
    """Resolver explains nested path and result when high-income branch matches."""

    ctx: Mapping[str, Any] = {
        "income_level": "HIGH",
        "credit_score": 720,
        "loan_purpose": "AUTO",
    }

    explanation = credit_scoring_resolver.explain(ctx)

    assert explanation.matched_rule == "High income"
    assert explanation.path == ["High income", "Top tier approval"]
    assert explanation.tested == ["High income: ✓"]
    assert explanation.result == LoanDecision(decision="APPROVE", rate=3.5)


def test_explain_fallback_path(credit_scoring_resolver) -> None:
    """Resolver explains how it falls back to the default branch when nothing matches."""

    ctx: Mapping[str, Any] = {
        "income_level": "LOW",
        "loan_purpose": "AUTO",
        "credit_score": 550,
    }

    explanation = credit_scoring_resolver.explain(ctx)

    assert explanation.matched_rule == "Default review"
    assert explanation.path == ["Default review"]
    assert explanation.tested == [
        "High income: ×",
        "Medium mortgage: ×",
        "Low credit reject: ×",
        "Default review: ✓",
    ]
    assert explanation.result == LoanDecision(decision="REVIEW", rate=None)


def test_explain_nested_fallback(credit_scoring_resolver) -> None:
    """Explain returns the fallback path inside nested subrules."""

    ctx: Mapping[str, Any] = {
        "income_level": "HIGH",
        "credit_score": 850,
    }

    explanation = credit_scoring_resolver.explain(ctx)

    assert explanation.matched_rule == "High income"
    assert explanation.path == ["High income", "High income fallback"]
    assert explanation.result == LoanDecision(decision="REVIEW", rate=7.0)


def test_explain_no_match_returns_empty_result(credit_scoring_ruleset) -> None:
    """Ruleset without otherwise clause reports tested rules but no match."""

    resolver = ruleset(
        when(income_level == "HIGH", name="High income").then(credit_scoring_ruleset),
    ).to_resolver()

    ctx: Mapping[str, Any] = {"income_level": "LOW"}
    explanation = resolver.explain(ctx)

    assert explanation.matched_rule is None
    assert explanation.result is None
    assert explanation.path == []
    assert explanation.tested == ["High income: ×"]
