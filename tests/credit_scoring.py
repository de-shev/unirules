"""Shared fixtures and utilities for credit-scoring related tests."""

from __future__ import annotations

from typing import Optional, TypedDict

from unirules import Resolver, RuleSet, field, otherwise, ruleset, when
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.interval.domain import IntervalDomain


class LoanDecision(TypedDict):
    """Structure of the decision produced by the credit scoring resolver."""

    decision: str
    rate: Optional[float]


credit_score = field("credit_score", IntervalDomain(300, 850))
income_level = field("income_level", DiscreteDomain({"LOW", "MEDIUM", "HIGH"}))
loan_purpose = field(
    "loan_purpose",
    DiscreteDomain({"MORTGAGE", "AUTO", "PERSONAL"}),
)


def build_high_income_ruleset() -> RuleSet[LoanDecision]:
    """Construct the nested ruleset used for ``HIGH`` income applicants."""

    return ruleset(
        when(credit_score.between(700, 850), name="Top tier approval").then(LoanDecision(decision="APPROVE", rate=3.5)),
        when(credit_score.between(600, 699), name="Standard approval").then(LoanDecision(decision="APPROVE", rate=5.0)),
        otherwise(LoanDecision(decision="REVIEW", rate=7.0), name="High income fallback"),
    )


def build_credit_scoring_ruleset() -> RuleSet[LoanDecision]:
    """Return the full credit scoring ruleset used across tests."""

    high_income_subrules = build_high_income_ruleset()
    return ruleset(
        when(income_level == "HIGH", name="High income").then(high_income_subrules),
        when(
            (income_level == "MEDIUM") & (loan_purpose == "MORTGAGE"),
            name="Medium mortgage",
        ).then(LoanDecision(decision="APPROVE", rate=4.5)),
        when(credit_score < 500, name="Low credit reject").then(LoanDecision(decision="REJECT", rate=None)),
        otherwise(LoanDecision(decision="REVIEW", rate=None), name="Default review"),
    )


def build_credit_scoring_resolver() -> Resolver[LoanDecision]:
    """Create a resolver configured with the credit scoring ruleset."""

    return build_credit_scoring_ruleset().to_resolver()


__all__ = [
    "LoanDecision",
    "build_credit_scoring_resolver",
    "build_credit_scoring_ruleset",
    "build_high_income_ruleset",
    "credit_score",
    "income_level",
    "loan_purpose",
]
