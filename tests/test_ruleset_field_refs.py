from unirules import field, ruleset, when
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.interval.domain import IntervalDomain


def test_ruleset_collects_nested_field_refs() -> None:
    """RuleSet iterates unique field refs from nested subtrees."""

    status = field("status", DiscreteDomain({"VIP", "STD"}))
    channel = field("channel", DiscreteDomain({"web", "branch"}))
    amount = field("amount", IntervalDomain(0, 100))

    nested = ruleset(
        when(channel == "web").then("web"),
        when(amount.gt(10)).then("amount"),
    )

    top = ruleset(
        when(status == "VIP").then(nested),
        when(status == "STD").then("std"),
    )

    assert {ref.name for ref in top.iter_field_refs()} == {"status", "channel", "amount"}
