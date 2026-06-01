"""Importing this package registers every built-in rule.

Each module below calls ``@register`` at import time, so a single
``import overfitlint.rules`` populates the registry.
"""
from __future__ import annotations

# Rule modules are imported here for their registration side effects.
from . import (  # noqa: F401
    excessive_params,
    gate_stacking,
    hardcoded_anchors,
    hardcoded_tickers,
    magic_thresholds,
    param_encoded_name,
    rank_position_pick,
)
