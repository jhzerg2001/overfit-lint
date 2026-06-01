"""hardcoded-anchors: hardcoded performance targets / FUNNEL acceptance gates."""
from __future__ import annotations

import ast
import re

from ..core.context import AnalysisContext
from ..core.finding import Finding, Severity
from ..core.registry import register
from ..core.rule import Rule
from ._util import is_number, is_str, named_numbers

_NAME_PERF = re.compile(
    r"(?i)(reference|anchor|funnel|\bkpi\b|acceptance|min_return|max_dd|max_drawdown|"
    r"must_exceed|must_beat|expected_return|target_return|required_return|"
    r"benchmark_return|hist(orical)?_return|goal_return|ref_return|threshold_return)"
)
_NAME_STRONG = re.compile(r"(?i)(funnel|\bkpi\b|acceptance|reference|anchor)")
_DATE_STR = re.compile(r"\b(19|20)\d{2}(-\d{2}(-\d{2})?)?\b")


@register
class HardcodedAnchorsRule(Rule):
    rule_id = "hardcoded-anchors"
    summary = "hardcoded performance targets / FUNNEL acceptance gates"
    rationale = (
        "Binding a concrete return/drawdown number to a name like 'reference', "
        "'funnel' or 'min_return' writes a known historical result into the code "
        "as an acceptance gate — answer-copying, not a forward-looking rule."
    )

    def _date_lines(self, tree: ast.AST) -> set[int]:
        lines: set[int] = set()
        for n in ast.walk(tree):
            if is_str(n) and _DATE_STR.search(n.value):
                lines.add(n.lineno)
            elif is_number(n) and isinstance(n.value, int) and 1990 <= n.value <= 2100:
                lines.add(n.lineno)
        return lines

    def check(self, ctx: AnalysisContext) -> list[Finding]:
        out: list[Finding] = []
        seen: set[tuple[int, str]] = set()
        date_lines = self._date_lines(ctx.tree)
        for name, val_node, lineno in named_numbers(ctx.tree):
            if not _NAME_PERF.search(name):
                continue
            key = (lineno, name)
            if key in seen:
                continue
            seen.add(key)
            strong = bool(_NAME_STRONG.search(name))
            near_date = any(abs(lineno - d) <= 3 for d in date_lines)
            sev = Severity.CRITICAL if (strong or near_date) else Severity.WARNING
            out.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"hardcoded performance target {name!r} = {val_node.value!r}",
                    line=lineno,
                    col=getattr(val_node, "col_offset", 0),
                    snippet=ctx.snippet(lineno),
                    why=self.rationale,
                    evidence={"name": name, "value": val_node.value, "date_gated": near_date},
                )
            )
        return out
