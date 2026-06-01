"""param-encoded-name: identifiers/strings that encode grid-search provenance."""
from __future__ import annotations

import ast
import re

from ..core.context import AnalysisContext
from ..core.finding import Finding, Severity
from ..core.registry import register
from ..core.rule import Rule

# (regex, severity, message). Ordered: most specific first.
_PATTERNS: list[tuple[re.Pattern, Severity, str]] = [
    (re.compile(r"(?i)(?:source_candidate|backtest_anchor|top\d*_reference)"),
     Severity.CRITICAL, "names a search candidate / backtest anchor"),
    (re.compile(r"(?i)(?:champion|winner|grid_?search)"),
     Severity.WARNING, "brags about being a search winner"),
    (re.compile(r"(?i)iter\d+"),
     Severity.WARNING, "encodes a search-iteration number"),
    (re.compile(r"(?:_R\d+(?:_|$)|^R\d+_)"),
     Severity.WARNING, "encodes a search round (R<n>)"),
    (re.compile(r"(?i)vix\d{2,}"),
     Severity.WARNING, "hardcodes a VIX level into a name"),
    (re.compile(r"(?i)(?:best|final)_v?\d+"),
     Severity.WARNING, "encodes a versioned 'best' candidate"),
    (re.compile(r"\d+p\d+"),
     Severity.INFO, "encodes a decimal parameter in a name (e.g. 0p16 = 0.16)"),
]


def _named_texts(tree: ast.AST):
    """Yield (text, node) for identifiers, attribute names and string literals."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id, node
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.name, node
        elif isinstance(node, ast.arg):
            yield node.arg, node
        elif isinstance(node, ast.keyword) and node.arg:
            yield node.arg, node
        elif isinstance(node, ast.Attribute):
            yield node.attr, node
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value, node


@register
class ParamEncodedNameRule(Rule):
    rule_id = "param-encoded-name"
    summary = "identifiers/strings that encode grid-search provenance"
    rationale = (
        "Names like 'Q_R7_VIX78', 'best_v9_iter9' or 'champion' record that the "
        "value won a parameter search. That provenance is a direct fingerprint of "
        "multiple-testing / selection bias — the survivor of thousands of variants."
    )

    def check(self, ctx: AnalysisContext) -> list[Finding]:
        out: list[Finding] = []
        seen: set[tuple[int, str, str]] = set()
        for text, node in _named_texts(ctx.tree):
            if not isinstance(text, str) or not text or len(text) > 200:
                continue
            for rx, sev, msg in _PATTERNS:
                m = rx.search(text)
                if not m:
                    continue
                line = getattr(node, "lineno", 0)
                key = (line, text, msg)
                if key in seen:
                    break
                seen.add(key)
                out.append(
                    Finding(
                        rule_id=self.rule_id,
                        severity=sev,
                        message=f"{msg}: {text!r}",
                        line=line,
                        col=getattr(node, "col_offset", 0),
                        snippet=ctx.snippet(line) if line else "",
                        why=self.rationale,
                        evidence={"text": text, "match": m.group(0)},
                    )
                )
                break  # one finding per text node
        return out
