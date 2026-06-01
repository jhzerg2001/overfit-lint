"""magic-thresholds: suspiciously precise float thresholds / weights."""
from __future__ import annotations

import ast

from ..core.context import AnalysisContext
from ..core.finding import Finding, Severity
from ..core.registry import register
from ..core.rule import Rule
from ._util import is_number, sig_digits


@register
class MagicThresholdsRule(Rule):
    rule_id = "magic-thresholds"
    summary = "suspiciously precise numeric thresholds / weights"
    rationale = (
        "Thresholds and weights tuned to many significant digits (e.g. 0.085734, "
        "or a 16-decimal weight) are almost never derived from theory — they are "
        "optimizer output fitted to one history. Genuine edges survive round numbers."
    )

    def check(self, ctx: AnalysisContext) -> list[Finding]:
        out: list[Finding] = []
        seen: set[tuple[int, str]] = set()
        min_sig = ctx.config.magic_min_sig_digits
        for node in ast.walk(ctx.tree):
            if not is_number(node) or not isinstance(node.value, float):
                continue
            sig = sig_digits(node.value)
            if sig < min_sig:
                continue
            key = (node.lineno, repr(node.value))
            if key in seen:
                continue
            seen.add(key)
            if sig >= 10:
                sev = Severity.CRITICAL
            elif sig >= 6:
                sev = Severity.WARNING
            else:
                sev = Severity.INFO
            out.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"float literal {node.value!r} carries {sig} significant digits",
                    line=node.lineno,
                    col=node.col_offset,
                    snippet=ctx.snippet(node),
                    why=self.rationale,
                    evidence={"value": node.value, "sig_digits": sig},
                )
            )
        return out
