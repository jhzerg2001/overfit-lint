"""Rendering: turn results into text or JSON, and compute the smell score."""
from __future__ import annotations

import json
import math

from .finding import SEVERITY_WEIGHT, Severity

_SCORE_K = 12  # normalization constant; see design spec §7.

_SEV_COLOR = {Severity.INFO: "36", Severity.WARNING: "33", Severity.CRITICAL: "31"}


def smell_score(findings) -> int:
    """0–100 overfitting smell score: monotonic, saturating, 0 when clean.

    ``score = min(100, round(100 * (1 - exp(-weighted / K))))`` where
    ``weighted`` sums severity weights (info=1, warning=3, critical=8).
    """
    weighted = sum(SEVERITY_WEIGHT[f.severity] for f in findings if f.rule_id != "rule-error")
    if weighted <= 0:
        return 0
    return min(100, round(100 * (1 - math.exp(-weighted / _SCORE_K))))


def _color(text: str, code: str, on: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if on else text


def _counts(findings) -> str:
    by = {Severity.CRITICAL: 0, Severity.WARNING: 0, Severity.INFO: 0}
    for f in findings:
        if f.rule_id == "rule-error":
            continue
        by[f.severity] = by.get(f.severity, 0) + 1
    parts = [f"{n} {sev.label}" for sev, n in by.items() if n]
    return ", ".join(parts) if parts else "0"


def render_text(results, *, color: bool = False) -> str:
    """Human-readable report for one or more AnalysisResult objects."""
    out: list[str] = []
    for res in results:
        out.append(_color(f"overfit-lint: {res.path}", "1", color))
        if res.error:
            out.append(_color(f"  ! {res.error}", "31", color))
            out.append("")
            continue
        if not res.findings:
            out.append(_color("  clean — no overfitting smells detected", "32", color))
            out.append("  smell score 0/100")
            out.append("")
            continue
        for f in res.findings:
            tag = _color(f"[{f.severity.label}]", _SEV_COLOR.get(f.severity, "0"), color)
            loc = f"L{f.line}" if f.line else "file"
            out.append(f"  {loc} {tag} {f.rule_id}: {f.message}")
            if f.snippet:
                out.append(f"      | {f.snippet}")
            if f.why:
                out.append(f"      why: {f.why}")
        out.append("  " + "-" * 48)
        out.append(
            f"  {len(res.findings)} findings ({_counts(res.findings)})"
            f" — smell score {smell_score(res.findings)}/100"
        )
        out.append("")
    return ("\n".join(out).rstrip() + "\n") if out else ""


def render_json(results) -> str:
    """Machine-readable report (UTF-8, pretty-printed)."""
    payload = [
        {
            "path": res.path,
            "error": res.error,
            "score": smell_score(res.findings),
            "findings": [f.to_dict() for f in res.findings],
        }
        for res in results
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)
