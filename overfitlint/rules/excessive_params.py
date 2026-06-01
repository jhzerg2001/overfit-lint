"""excessive-params: too many free numeric parameters (degrees of freedom)."""
from __future__ import annotations

import ast

from ..core.context import AnalysisContext
from ..core.finding import Finding, Severity
from ..core.registry import register
from ..core.rule import Rule
from ._util import is_number, named_numbers


@register
class ExcessiveParamsRule(Rule):
    rule_id = "excessive-params"
    summary = "too many free numeric parameters for the data on hand"
    rationale = (
        "Every tunable number is a degree of freedom. Dozens of knobs on a few "
        "hundred days of data can memorise history rather than capture an edge. "
        "Pass --data-days to also check the parameters-per-data-day ratio."
    )

    def check(self, ctx: AnalysisContext) -> list[Finding]:
        cfg = ctx.config
        knobs: set[tuple[int, int]] = set()
        sample: list[str] = []
        for name, val_node, _lineno in named_numbers(ctx.tree):
            v = val_node.value
            if isinstance(v, bool) or v in (0, 1, -1):
                continue
            key = (val_node.lineno, val_node.col_offset)
            if key in knobs:
                continue
            knobs.add(key)
            if len(sample) < 8:
                sample.append(name)

        # Threshold constants inside comparisons are knobs too — each gate is a
        # degree of freedom (skip loop bounds compared against len()/range()).
        for node in ast.walk(ctx.tree):
            if not isinstance(node, ast.Compare):
                continue
            parts = [node.left] + list(node.comparators)
            if any(
                isinstance(p, ast.Call) and isinstance(p.func, ast.Name) and p.func.id in ("len", "range")
                for p in parts
            ):
                continue
            for p in parts:
                if is_number(p) and p.value not in (0, 1, -1):
                    knobs.add((p.lineno, p.col_offset))

        n = len(knobs)

        sev = None
        extra = ""
        if n > cfg.excessive_params_max:
            sev = Severity.CRITICAL if n > 2 * cfg.excessive_params_max else Severity.WARNING
        if ctx.data_days and n > 0:
            ratio = ctx.data_days / n
            if ratio < cfg.min_days_per_param:
                extra = f"; only {ratio:.1f} data-days per parameter (< {cfg.min_days_per_param})"
                if sev is None:
                    sev = Severity.WARNING
                elif sev is Severity.WARNING:
                    sev = Severity.CRITICAL
        if sev is None:
            return []

        return [
            Finding(
                rule_id=self.rule_id,
                severity=sev,
                message=(
                    f"~{n} numeric free parameters in this file"
                    f" (threshold {cfg.excessive_params_max}){extra}"
                ),
                line=1,
                col=0,
                snippet="",
                why=self.rationale,
                evidence={"count": n, "sample": sample, "data_days": ctx.data_days},
            )
        ]
