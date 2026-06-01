"""hardcoded-tickers: hardcoded symbol lists, especially blacklists / anchors."""
from __future__ import annotations

import ast
import re

from ..core.context import AnalysisContext
from ..core.finding import Finding, Severity
from ..core.registry import register
from ..core.rule import Rule
from ._util import collection_tickers, is_number, is_str

_NAME_TICKER = re.compile(r"(?i)(ticker|symbol|stock|universe|\bsyms?\b)")
_NAME_BAN = re.compile(r"(?i)(black_?list|banned?|\bban\b|exclude|deny|avoid|\bskip\b|never|drop)")
_DATE_STR = re.compile(r"\b(19|20)\d{2}(-\d{2}(-\d{2})?)?\b")


@register
class HardcodedTickersRule(Rule):
    rule_id = "hardcoded-tickers"
    summary = "hardcoded ticker lists (blacklists, anchors, OOS exclusions)"
    rationale = (
        "Hardcoding specific tickers — especially a blacklist gated on an "
        "out-of-sample date, or a single 'winner' anchor — copies known history "
        "into the code. The names were picked for what they did, not from a rule."
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
        seen: set[int] = set()
        date_lines = self._date_lines(ctx.tree)
        for node in ast.walk(ctx.tree):
            tickers: list[str] = []
            names: list[str] = []
            if isinstance(node, ast.Assign):
                tickers = collection_tickers(node.value)
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                tickers = collection_tickers(node.value)
                if isinstance(node.target, ast.Name):
                    names = [node.target.id]
            elif isinstance(node, (ast.Set, ast.List, ast.Tuple)):
                tickers = collection_tickers(node)
            else:
                continue
            if not tickers:
                continue
            line = node.lineno
            if line in seen:
                continue
            joined = " ".join(names)
            ban = bool(_NAME_BAN.search(joined))
            tickerish = bool(_NAME_TICKER.search(joined))
            near_date = any(abs(line - d) <= 3 for d in date_lines)
            # Require corroboration to avoid flagging incidental upper-case lists.
            if not (ban or tickerish or near_date or len(tickers) >= 3):
                continue
            seen.add(line)
            sev = Severity.CRITICAL if (ban or near_date) else Severity.WARNING
            sample = ", ".join(tickers[:6])
            out.append(
                Finding(
                    rule_id=self.rule_id,
                    severity=sev,
                    message=f"hardcoded ticker list ({len(tickers)}): {sample}",
                    line=line,
                    col=node.col_offset,
                    snippet=ctx.snippet(line),
                    why=self.rationale,
                    evidence={"tickers": tickers, "names": names, "date_gated": near_date},
                )
            )
        return out
