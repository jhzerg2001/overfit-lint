"""The runner: parse a file once, run the rules, collect findings safely."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .context import AnalysisContext
from .finding import Finding, Severity
from ..config import RuleConfig


@dataclass
class AnalysisResult:
    """Outcome for one file: its findings, or a file-level error."""

    path: str
    findings: list[Finding] = field(default_factory=list)
    error: str | None = None


def _default_rules():
    # Imported lazily so importing the package has no surprising side effects,
    # and to avoid any import-order coupling with the rules package.
    from .. import rules as _rules  # noqa: F401  (import triggers registration)
    from .registry import all_rules

    return all_rules()


def analyze_source(
    source: str,
    path: str = "<string>",
    *,
    data_days: int | None = None,
    config: RuleConfig | None = None,
    rules=None,
    select: set[str] | None = None,
    ignore: set[str] | None = None,
) -> AnalysisResult:
    """Analyze source text. Never raises on bad input — returns an error result.

    Args:
        rules: explicit list of rule instances (defaults to the global registry).
               Passing a list keeps tests isolated from the registry.
        select/ignore: optional rule-id filters.
    """
    try:
        ctx = AnalysisContext.from_source(source, path, data_days, config)
    except SyntaxError as exc:
        return AnalysisResult(path=path, findings=[], error=f"syntax error: {exc.msg} (line {exc.lineno})")

    if rules is None:
        rules = _default_rules()

    findings: list[Finding] = []
    for rule in rules:
        if select and rule.rule_id not in select:
            continue
        if ignore and rule.rule_id in ignore:
            continue
        try:
            findings.extend(rule.check(ctx) or [])
        except Exception as exc:  # one bad rule must not kill the whole run
            findings.append(
                Finding(
                    rule_id="rule-error",
                    severity=Severity.INFO,
                    message=f"rule {rule.rule_id!r} raised internally: {exc}",
                    line=0,
                    why="A rule failed; analysis continued without it. Please report this.",
                    evidence={"rule": rule.rule_id, "error": str(exc)},
                )
            )
    findings.sort(key=lambda f: (f.line, f.col, f.rule_id))
    return AnalysisResult(path=path, findings=findings, error=None)


def analyze_path(
    path: str,
    *,
    data_days: int | None = None,
    config: RuleConfig | None = None,
    rules=None,
    select: set[str] | None = None,
    ignore: set[str] | None = None,
) -> AnalysisResult:
    """Read a file and analyze it. Reports IO problems as a file-level error."""
    if not os.path.isfile(path):
        return AnalysisResult(path=path, findings=[], error="file not found")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        return AnalysisResult(path=path, findings=[], error=f"cannot read file: {exc}")
    return analyze_source(
        source, path, data_days=data_days, config=config, rules=rules, select=select, ignore=ignore
    )
