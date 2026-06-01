"""A deliberately *over-fitted* strategy — the positive example (synthetic).

Every block below is a textbook overfitting tell, so overfit-lint lights up
across all seven rules. This file is fictional: it contains no real strategy,
only the shapes of the smells the linter looks for.

    $ overfit-lint examples/overfit_example.py
"""
from __future__ import annotations

OOS_START = "2026-01-31"

# hardcoded-anchors: known historical results written in as acceptance gates
top1_reference_full_return_pct = 414.45
FUNNEL_2024_min_return = 85.0

# param-encoded-name: grid-search provenance baked into the names
source_candidate = "Q_R7_VIX78"
best_v9_iter9_weight = 0.3569571510008239  # magic-thresholds: 16-decimal weight

# hardcoded-tickers: an out-of-sample blacklist gated on a date
BANNED_TICKERS = {"SNDK", "LITE", "HL", "WDC", "TER"}

# rank-position-pick: a tuned mid-rank, encoded as a parameter
rank_start = 15

# excessive-params: far too many knobs for a few months of data
WEIGHTS = {
    "mom": 0.31, "rev": 0.22, "vol": 0.17, "liq": 0.13,
    "qqq": 0.09, "vix": 0.05, "brd": 0.03,
}


def eligible(row):
    # gate-stacking + magic-thresholds: a wall of precise threshold gates
    return (
        row.vix_rank <= 0.7834
        and row.ret_21d >= 0.0345
        and row.ret_63d >= 0.1287
        and row.vol_21d <= 0.0856
        and row.close_pos_63d >= 0.9123
        and row.turnover >= 0.0412
        and row.qqq_gap >= 0.0237
        and row.id21 >= 0.4561
        and row.nh63 >= 0.8534
    )


def select(ranked):
    # rank-position-pick: skip the top, take the 16th-ranked name
    return ranked.iloc[15]
