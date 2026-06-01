"""rank-position-pick: systematically selecting a fixed mid-rank, skipping the top."""
from __future__ import annotations

import ast
import re

from ..core.context import AnalysisContext
from ..core.finding import Finding, Severity
from ..core.registry import register
from ..core.rule import Rule
from ._util import int_const, name_hint, named_numbers

_RANK_PARAM = re.compile(
    r"(?i)(rank_start|rank_slot|rank_pos(ition)?|rank_index|rank_idx|"
    r"selection_rank|pick_rank|start_rank|nth_rank|rank_n)"
)
_RANKED_HINT = re.compile(
    r"(?i)(ranked|ranking|rank|sorted|nlargest|nsmallest|scores?|"
    r"momentum|leaders?|candidates?|cands?)"
)
_ARGSORT = re.compile(r"(?i)arg(sort|partition)")
_RANK_NAME = re.compile(r"(?i)(^rank$|_rank$|^rank_)")


@register
class RankPositionPickRule(Rule):
    rule_id = "rank-position-pick"
    summary = "selecting a fixed mid-rank instead of the top"
    rationale = (
        "Sorting candidates by a score and then systematically taking, say, the "
        "6th or 15th — skipping the top — has no economic justification. If the "
        "mid-rank wins in backtest it is almost certainly pure curve-fitting."
    )

    def _mk(self, sev, msg, node, ctx, evidence):
        line = getattr(node, "lineno", 0)
        return Finding(
            rule_id=self.rule_id, severity=sev, message=msg,
            line=line, col=getattr(node, "col_offset", 0),
            snippet=ctx.snippet(line), why=self.rationale, evidence=evidence,
        )

    def check(self, ctx: AnalysisContext) -> list[Finding]:
        out: list[Finding] = []

        # 1) a parameter literally named like a rank position, set to >= 3
        for name, val_node, _lineno in named_numbers(ctx.tree):
            v = val_node.value
            if isinstance(v, bool) or not isinstance(v, int):
                continue
            if _RANK_PARAM.search(name) and v >= 3:
                out.append(self._mk(
                    Severity.CRITICAL,
                    f"parameter {name!r} = {v} selects a fixed mid-rank (skips the top {v - 1})",
                    val_node, ctx, {"param": name, "rank": v},
                ))

        # 2/3) subscripts picking a fixed non-top position of a ranked sequence
        for node in ast.walk(ctx.tree):
            if isinstance(node, ast.Subscript):
                base_is_argsort = isinstance(node.value, ast.Call) and bool(
                    _ARGSORT.search(name_hint(node.value.func) or "")
                )
                if not (base_is_argsort or _RANKED_HINT.search(name_hint(node.value))):
                    continue
                sl = node.slice
                if isinstance(sl, ast.Slice):
                    low = int_const(sl.lower)
                    if low is not None and low >= 2:
                        sev = Severity.CRITICAL if low >= 5 else Severity.WARNING
                        out.append(self._mk(
                            sev, f"slices off the top {low} ranked items (starts at index {low})",
                            node, ctx, {"start": low},
                        ))
                else:
                    idx = int_const(sl)
                    if idx is not None and idx >= 2:
                        sev = Severity.CRITICAL if idx >= 5 else Severity.WARNING
                        out.append(self._mk(
                            sev,
                            f"picks ranked item #{idx + 1} (index {idx}), skipping the top {idx}",
                            node, ctx, {"index": idx},
                        ))

            # 4) keeping only a fixed mid-rank: `rank == k` (k >= 3)
            elif isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq):
                left, right = node.left, node.comparators[0]
                for a, b in ((left, right), (right, left)):
                    if isinstance(a, ast.Name) and _RANK_NAME.search(a.id):
                        k = int_const(b)
                        if k is not None and k >= 3:
                            sev = Severity.CRITICAL if k >= 5 else Severity.WARNING
                            out.append(self._mk(
                                sev, f"keeps only rank == {k} (a fixed mid-rank, not the top)",
                                node, ctx, {"rank": k},
                            ))
                            break

        # de-duplicate identical hits, keep stable order
        uniq: dict[tuple, Finding] = {}
        for f in out:
            uniq.setdefault((f.line, f.col, f.message), f)
        return sorted(uniq.values(), key=lambda f: (f.line, f.col))
