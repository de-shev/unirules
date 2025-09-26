"""Symbolic analysis tests for discrete and interval rulesets."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from unirules import RuleSetPolicy, field, otherwise, ruleset, when
from unirules.domains.discrete.domain import DiscreteDomain
from unirules.domains.discrete.values import DiscreteSet
from unirules.domains.interval.domain import IntervalDomain
from unirules.domains.interval.values import IntervalSet


def _normalize_entries(entries: list[tuple[tuple[int, ...], Any, Any]]) -> list[tuple[tuple[int, ...], Any, Any]]:
    """Convert value sets inside ``analysis.by_rule`` into python primitives."""

    normalized: list[tuple[tuple[int, ...], Any, Any]] = []
    for index_path, value_set, payload in entries:
        if isinstance(value_set, DiscreteSet):
            normalized.append((index_path, set(value_set.vals), payload))
        elif isinstance(value_set, IntervalSet):
            normalized.append((index_path, tuple(value_set.segs), payload))
        else:
            normalized.append((index_path, value_set, payload))
    return normalized


def _build_country_ruleset():
    country = field(
        "country",
        domain=DiscreteDomain({"US", "RU", "IT", "NL", "FR"}),
    )
    program = field("program", domain=DiscreteDomain({"VIP", "STD"}))

    analyzer = ruleset(
        when(program.equals("VIP") & country.isin({"US", "RU", "IT"})).then("A"),
        when(program.equals("VIP") & country.equals("NL")).then("B"),
        when(program.equals("STD") & country.equals("FR")).then("C"),
    ).to_analyzer()

    return analyzer, country


def test_discrete_analysis_filters_by_context() -> None:
    """Context constrains analysis to matching branches while preserving order."""

    analyzer, country = _build_country_ruleset()

    analysis = analyzer.analyze(target=country, ctx={"program": "VIP"})

    assert analysis.covered_values() == {"US", "RU", "IT", "NL"}
    assert analysis.uncovered_values() == {"FR"}
    assert _normalize_entries(analysis.by_rule) == [
        ((0,), {"US", "RU", "IT"}, "A"),
        ((1,), {"NL"}, "B"),
    ]


@pytest.mark.parametrize(
    "ctx",
    [
        pytest.param({"program": "VIP"}, id="program-only"),
        pytest.param({"program": "VIP", "country": "US"}, id="with-target-in-ctx"),
    ],
)
def test_discrete_analysis_ignores_target_value_in_context(ctx: Mapping[str, Any]) -> None:
    """Including the target field in the context must not narrow the projection."""

    analyzer, country = _build_country_ruleset()

    analysis = analyzer.analyze(target=country, ctx=ctx)

    assert analysis.covered_values() == {"US", "RU", "IT", "NL"}
    assert analysis.uncovered_values() == {"FR"}


def test_excluded_via_not_in() -> None:
    """NOT IN conditions contribute with the complement of the restricted values."""

    country = field("country", domain=DiscreteDomain({"US", "RU", "IT"}))
    program = field("program", domain=DiscreteDomain({"VIP", "STD"}))

    analyzer = ruleset(
        when(program.equals("STD") & country.notin({"US", "RU"})).then("OK"),
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={"program": "STD"})

    assert analysis.covered_values() == {"IT"}
    assert analysis.uncovered_values() == {"US", "RU"}


def test_contradictory_rule_is_skipped() -> None:
    """Rules with contradictory projections should not contribute coverage."""

    country = field("country", domain=DiscreteDomain({"US", "RU"}))
    program = field("program", domain=DiscreteDomain({"VIP", "STD"}))

    analyzer = ruleset(
        when(program.equals("VIP") & country.equals("US") & ~country.isin({"US"})).then("X"),
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={"program": "VIP"})

    assert analysis.covered_values() == set()
    assert analysis.uncovered_values() == {"US", "RU"}
    assert analysis.by_rule == []


def test_overlapping_rules_first_wins() -> None:
    """First matching rule consumes the intersection leaving later rules empty."""

    country = field("country", domain=DiscreteDomain({"US", "RU", "FR"}))

    analyzer = ruleset(
        when(country.isin({"US", "RU"})).then("A"),
        when(country.equals("US")).then("B"),
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={})

    assert analysis.covered_values() == {"US", "RU"}
    assert analysis.uncovered_values() == {"FR"}
    assert _normalize_entries(analysis.by_rule) == [((0,), {"US", "RU"}, "A")]


def test_overlapping_rules_priority_policy() -> None:
    """Priority policy allows later rules to override earlier matches."""

    country = field("country", domain=DiscreteDomain({"US", "RU"}))

    analyzer = ruleset(
        when(country.isin({"US", "RU"}), name="broad", priority=0).then("A"),
        when(country.equals("US"), name="specific", priority=10).then("B"),
        policy="priority",
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={})

    assert analysis.covered_values() == {"US", "RU"}
    assert analysis.uncovered_values() == set()
    assert _normalize_entries(analysis.by_rule) == [
        ((1,), {"US"}, "B"),
        ((0,), {"RU"}, "A"),
    ]


def test_nested_ruleset_priority_policy() -> None:
    """Priority policy applies within nested rulesets during analysis."""

    country = field("country", domain=DiscreteDomain({"US", "RU", "NL"}))
    program = field("program", domain=DiscreteDomain({"VIP", "STD"}))

    analyzer = ruleset(
        when(program.equals("VIP"), name="vip", priority=1).then(
            ruleset(
                when(country.isin({"US", "RU"}), name="broad", priority=0).then("A"),
                when(country.equals("US"), name="specific", priority=10).then("B"),
                policy=RuleSetPolicy.PRIORITY,
            )
        ),
        when(program.equals("STD"), name="std", priority=5).then("STD"),
        policy=RuleSetPolicy.PRIORITY,
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={"program": "VIP"})

    assert analysis.covered_values() == {"US", "RU"}
    assert analysis.uncovered_values() == {"NL"}
    assert _normalize_entries(analysis.by_rule) == [
        ((0, 1), {"US"}, "B"),
        ((0, 0), {"RU"}, "A"),
    ]


def test_nested_ruleset_projection() -> None:
    """Nested rules inherit context filters and report index paths."""

    country = field("country", domain=DiscreteDomain({"US", "RU", "NL", "FR"}))
    program = field("program", domain=DiscreteDomain({"VIP", "STD"}))

    analyzer = ruleset(
        when(program.equals("VIP")).then(
            ruleset(
                when(country.isin({"US", "RU"}), name="North").then(1),
                when(country.equals("NL"), name="Dutch").then(2),
            )
        ),
        when(program.equals("STD") & country.equals("FR")).then(3),
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={"program": "VIP"})

    assert analysis.covered_values() == {"US", "RU", "NL"}
    assert analysis.uncovered_values() == {"FR"}
    assert _normalize_entries(analysis.by_rule) == [
        ((0, 0), {"US", "RU"}, 1),
        ((0, 1), {"NL"}, 2),
    ]


def test_analysis_ignores_unknown_context_keys() -> None:
    """Context keys without known domains are ignored by the analyzer."""

    country = field("country", domain=DiscreteDomain({"US", "RU"}))

    analyzer = ruleset(
        when(country.equals("US")).then("US"),
        when(country.equals("RU")).then("RU"),
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={"timezone": "UTC"})

    assert analysis.covered_values() == {"US", "RU"}
    assert analysis.uncovered_values() == set()


def test_intervals_projection() -> None:
    """Interval analysis returns covered and uncovered segments."""

    amount = field("amount", domain=IntervalDomain(0, 200))

    analyzer = ruleset(
        when(amount.between(0, 90.0, closed="right")).then("LOW"),
        when(amount.between(100, 150, closed="both")).then("MID"),
    ).to_analyzer()

    analysis = analyzer.analyze(target=amount, ctx={})

    assert analysis.covered_values() == [
        (0.0, 90.0, "right"),
        (100.0, 150.0, "both"),
    ]
    assert set(analysis.uncovered_values()) == {
        (90.0, 100.0, "none"),
        (150.0, 200.0, "none"),
    }


def test_interval_analysis_respects_context_filters() -> None:
    """Context filters prune unmatched branches for interval targets."""

    amount = field("amount", domain=IntervalDomain(0, 300))
    program = field("program", domain=DiscreteDomain({"VIP", "STD"}))

    analyzer = ruleset(
        when(program.equals("VIP")).then(
            ruleset(
                when(amount.between(0, 100, closed="right")).then("VIP-LOW"),
                when(amount.between(100, 200, closed="both")).then("VIP-MID"),
            )
        ),
        when(program.equals("STD")).then(
            ruleset(
                when(amount.between(50, 150, closed="both")).then("STD-MID"),
                when(amount.between(200, 250, closed="left")).then("STD-HIGH"),
            )
        ),
    ).to_analyzer()

    analysis = analyzer.analyze(target=amount, ctx={"program": "VIP"})

    assert analysis.covered_values() == [
        (0.0, 200.0, "both"),
    ]
    assert set(analysis.uncovered_values()) == {
        (200.0, 300.0, "none"),
    }
    assert _normalize_entries(analysis.by_rule) == [
        ((0, 0), ((0.0, 100.0, "right"),), "VIP-LOW"),
        ((0, 1), ((100.0, 200.0, "right"),), "VIP-MID"),
    ]


def test_included_excluded_with_otherwise() -> None:
    """Fallback branch covers the remaining portion of the universe."""

    country = field("country", domain=DiscreteDomain({"US", "RU", "FR"}))

    analyzer = ruleset(
        when(country.isin({"US", "RU"})).then("A"),
        otherwise("DEFAULT"),
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={})

    assert analysis.covered_values() == {"US", "RU", "FR"}
    assert analysis.uncovered_values() == set()
    assert _normalize_entries(analysis.by_rule) == [
        ((0,), {"US", "RU"}, "A"),
        ((1,), {"FR"}, "DEFAULT"),
    ]


def test_three_fields_context_projects_third() -> None:
    """With three fields in rules, providing two in ctx yields projection on the third.

    The rules depend on: program, segment, and country. We analyze the country
    domain while constraining program and segment via context. Only rules whose
    non-target conditions match the ctx should contribute to coverage.
    """

    country = field("country", domain=DiscreteDomain({"US", "NL", "RU", "FR"}))
    program = field("program", domain=DiscreteDomain({"VIP", "STD"}))
    segment = field("segment", domain=DiscreteDomain({"B2B", "B2C"}))

    analyzer = ruleset(
        when(program.equals("VIP") & segment.equals("B2B") & country.isin({"US", "NL"})).then("X"),
        when(program.equals("VIP") & segment.equals("B2C") & country.equals("RU")).then("Y"),
        when(program.equals("STD") & segment.equals("B2B") & country.equals("FR")).then("Z"),
    ).to_analyzer()

    analysis = analyzer.analyze(target=country, ctx={"program": "VIP", "segment": "B2B"})

    assert analysis.covered_values() == {"US", "NL"}
    assert analysis.uncovered_values() == {"RU", "FR"}
    assert _normalize_entries(analysis.by_rule) == [
        ((0,), {"US", "NL"}, "X"),
    ]
