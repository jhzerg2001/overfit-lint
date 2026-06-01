"""The unit of output: a Finding, plus the Severity scale used everywhere."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class Severity(enum.IntEnum):
    """Ordered severity. IntEnum so ``--fail-on warning`` is a simple ``>=``."""

    INFO = 1
    WARNING = 2
    CRITICAL = 3

    @property
    def label(self) -> str:
        return self.name.lower()

    @classmethod
    def from_name(cls, name: str) -> "Severity":
        try:
            return cls[name.strip().upper()]
        except KeyError as exc:
            valid = ", ".join(s.label for s in cls)
            raise ValueError(f"unknown severity {name!r}; expected one of {valid}") from exc


# Weights used by the smell score. Documented in the design spec; deliberately
# simple so the score itself is not an opaque magic number.
SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.INFO: 1,
    Severity.WARNING: 3,
    Severity.CRITICAL: 8,
}


@dataclass(frozen=True)
class Finding:
    """One hit reported by a rule.

    Attributes:
        rule_id:  stable id of the rule (e.g. ``"magic-thresholds"``).
        severity: how strong the signal is.
        message:  one-line human summary of *this* hit.
        line:     1-based source line (0 = file-level / unknown).
        col:      0-based column offset.
        snippet:  the offending source line, stripped.
        why:      one-line explanation of why this is an overfitting tell.
        evidence: structured details (e.g. the literal value that triggered it).
    """

    rule_id: str
    severity: Severity
    message: str
    line: int
    col: int = 0
    snippet: str = ""
    why: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.label,
            "message": self.message,
            "line": self.line,
            "col": self.col,
            "snippet": self.snippet,
            "why": self.why,
            "evidence": self.evidence,
        }
