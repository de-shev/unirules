from decimal import Decimal

import pytest

from unirules import field, ruleset, when
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.interval.domain import IntervalDomain
from unirules.engines._ctx_validation import validate_context


def test_validate_context_normalizes_numeric_values() -> None:
    """Context validation coerces interval values and preserves discrete ones."""

    score = field("score", IntervalDomain(0, 100))
    status = field("status", DiscreteDomain({"LOW", "HIGH"}))

    rs = ruleset(
        when(score.gt(50)).then("high"),
        when(status == "HIGH").then("status"),
    )

    ctx = {"score": Decimal("75.5"), "status": "HIGH"}
    normalized = validate_context(rs, ctx)

    assert normalized is not ctx
    assert isinstance(normalized["score"], float)
    assert normalized["score"] == pytest.approx(75.5)
    assert normalized["status"] == "HIGH"
    # Original context remains untouched
    assert ctx["score"] == Decimal("75.5")
