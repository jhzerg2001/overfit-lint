"""gate-stacking: too many numeric threshold gates on one decision path."""
from __future__ import annotations

import ast

from ..core.context import AnalysisContext
from ..core.finding import Finding, Severity
from ..core.registry import register
from ..core.rule import Rule
from ._util import is_number


def _is_threshold_compare(node: ast.Compare) -> bool:
    parts = [node.left] + list(node.comparators)
    has_num = any(is_number(p) and p.value not in (0, 1, -1) for p in parts)
    has_feature = any(isinstance(p, (ast.Name, ast.Attribute, ast.Subscript)) for p in parts)
    # ignore comparisons against len(...) / range(...) — loop bounds, not gates.
    has_len_range = any(
        isinstance(p, ast.Call) and isinstance(p.func, ast.Name) and p.func.id in ("len", "range")
        for p in parts
    )
    return has_num and has_feature and not has_len_range


@register
class GateStackingRule(Rule):
    rule_id = "gate-stacking"
    summary = "a single function stacks many numeric threshold gates"
    rationale = (
        "Each eligibility gate (a feature compared to a tuned constant) is "
        "another degree of freedom. Stacking many lets a strategy carve history "
        "into exactly the right slices — flexibility that rarely survives live."
    )

    def check(self, ctx: AnalysisContext) -> list[Finding]:
        out: list[Finding] = []
        cfg = ctx.config
        for node in ast.walk(ctx.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            gates = sum(
                1
                for sub in ast.walk(node)
                if isinstance(sub, ast.Compare) and _is_threshold_compare(sub)
            )
            if gates > cfg.gate_stacking_max:
                sev = Severity.CRITICAL if gates > 2 * cfg.gate_stacking_max else Severity.WARNING
                out.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=sev,
                        message=f"function {node.name!r} stacks {gates} numeric threshold gates",
                        line=node.lineno,
                        col=node.col_offset,
                        snippet=ctx.snippet(node.lineno),
                        why=self.rationale,
                        evidence={"function": node.name, "gates": gates},
                    )
                )
        return out
