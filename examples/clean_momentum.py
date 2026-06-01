"""A small, deliberately *clean* momentum strategy — the negative example.

overfit-lint should report no warnings or criticals here: round thresholds,
few parameters, top-ranked selection, and no hardcoded history.

    $ overfit-lint examples/clean_momentum.py
"""
from __future__ import annotations

LOOKBACK_DAYS = 63
HOLD_DAYS = 5
MIN_DOLLAR_VOLUME = 20_000_000
TOP_K = 1


def momentum_score(prices):
    """Total return over the lookback window."""
    return prices[-1] / prices[-LOOKBACK_DAYS] - 1.0


def is_liquid(dollar_volume):
    return dollar_volume > MIN_DOLLAR_VOLUME


def select(candidates):
    """Rank by momentum and take the single strongest liquid name."""
    liquid = [c for c in candidates if is_liquid(c.dollar_volume)]
    ranked = sorted(liquid, key=lambda c: momentum_score(c.prices), reverse=True)
    return ranked[:TOP_K]
