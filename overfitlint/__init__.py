"""overfit-lint: a static analyzer that flags backtest-overfitting code smells.

It reads quant-strategy *source code* (without running it) and reports the
tells of an over-fitted research process: magic thresholds, search-encoded
names, hardcoded tickers/anchors, mid-rank picks, excessive free parameters,
gate stacking and FUNNEL-style acceptance gates.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .core.finding import Finding, Severity
from .core.context import AnalysisContext
from .core.runner import AnalysisResult, analyze_path, analyze_source
from .core.report import render_json, render_text, smell_score

__all__ = [
    "__version__",
    "Finding",
    "Severity",
    "AnalysisContext",
    "AnalysisResult",
    "analyze_source",
    "analyze_path",
    "render_text",
    "render_json",
    "smell_score",
]
