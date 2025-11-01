import pytest

from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.interval.domain import IntervalDomain
from unirules.dsl import field


def test_interval_between_raises_when_bounds_outside_domain() -> None:
    credit_score = field("credit_score", IntervalDomain(300, 850))

    with pytest.raises(ValueError):
        credit_score.between(200, 400)

    with pytest.raises(ValueError):
        credit_score.between(600, 900)


def test_interval_comparison_raises_when_threshold_outside_domain() -> None:
    credit_score = field("credit_score", IntervalDomain(300, 850))

    with pytest.raises(ValueError):
        credit_score.gt(900)

    with pytest.raises(ValueError):
        credit_score.lt(200)


def test_discrete_equality_raises_when_value_not_in_domain() -> None:
    income_level = field("income_level", DiscreteDomain({"LOW", "MEDIUM", "HIGH"}))

    with pytest.raises(ValueError):
        _ = income_level == "WRONG_VALUE"


def test_discrete_membership_raises_when_item_not_in_domain() -> None:
    income_level = field("income_level", DiscreteDomain({"LOW", "MEDIUM", "HIGH"}))

    with pytest.raises(ValueError):
        income_level.isin(["LOW", "INVALID"])
