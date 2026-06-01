"""Base class every rule inherits from."""
from __future__ import annotations

from .context import AnalysisContext
from .finding import Finding, Severity


class Rule:
    """A single overfitting-smell check.

    Subclasses set the class attributes and implement :meth:`check`. Each rule
    is an independent unit: it only reads the context and returns findings, so
    it can be understood and tested in isolation.
    """

    #: stable identifier, e.g. ``"magic-thresholds"`` (also the CLI selector).
    rule_id: str = ""
    #: one-line summary shown in ``--explain`` headers.
    summary: str = ""
    #: why a hit indicates overfitting; reused as ``Finding.why`` and ``--explain``.
    rationale: str = ""
    #: default severity a hit reports unless the rule decides otherwise.
    default_severity: Severity = Severity.WARNING

    def check(self, ctx: AnalysisContext) -> list[Finding]:  # pragma: no cover
        raise NotImplementedError
