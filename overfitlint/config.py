"""Tunable knobs shared by rules.

Kept tiny on purpose (YAGNI). Thresholds live here so they are documented in
one place and overridable from the CLI, rather than scattered as magic numbers
inside the rules — which would be ironic for this particular tool.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuleConfig:
    # excessive-params: warn once a single file exposes more than this many
    # numeric "knobs" (module constants, numeric default args, config values).
    excessive_params_max: int = 15

    # gate-stacking: warn once a single decision path stacks more than this
    # many threshold comparisons (each gate is another degree of freedom).
    gate_stacking_max: int = 8

    # magic-thresholds: minimum number of *significant digits* in a float
    # literal before it is treated as "suspiciously precise".
    magic_min_sig_digits: int = 3

    # excessive-params, optional data-aware check: when --data-days is given,
    # flag if there are fewer than this many data days per free parameter.
    min_days_per_param: int = 20
