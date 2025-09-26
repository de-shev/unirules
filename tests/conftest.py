"""Pytest fixtures shared across the test-suite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from .credit_scoring import LoanDecision, build_credit_scoring_resolver  # noqa: E402


@pytest.fixture
def credit_scoring_resolver():
    """Return a resolver configured for the credit scoring scenarios."""

    return build_credit_scoring_resolver()


__all__ = ["LoanDecision", "credit_scoring_resolver"]
