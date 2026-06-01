"""Command-line interface for overfit-lint."""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .core.finding import Severity
from .core.registry import all_rules, get_rule
from .core.report import render_json, render_text
from .core.runner import analyze_path


def _load_rules() -> None:
    """Populate the rule registry (import has registration side effects)."""
    from . import rules as _rules  # noqa: F401


def _split(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {item.strip() for item in value.split(",") if item.strip()}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="overfit-lint",
        description="Flag backtest-overfitting code smells in quant-strategy source.",
    )
    parser.add_argument("paths", nargs="*", help="Python source files to scan")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--fail-on",
        choices=[s.label for s in Severity],
        default="warning",
        help="exit 1 if any finding is at least this severe (default: warning)",
    )
    parser.add_argument(
        "--data-days",
        type=int,
        default=None,
        help="training-data days; enables the parameters-per-data-day check",
    )
    parser.add_argument("--select", default=None, help="comma-separated rule ids to run exclusively")
    parser.add_argument("--ignore", default=None, help="comma-separated rule ids to skip")
    parser.add_argument(
        "--explain",
        metavar="RULE",
        default=None,
        help="print a rule's rationale and exit ('all' lists every rule)",
    )
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colours")
    parser.add_argument("--version", action="version", version=f"overfit-lint {__version__}")
    return parser


def _explain(rule_id: str) -> int:
    if rule_id == "all":
        print("\n".join(f"{r.rule_id}\n    {r.summary}" for r in all_rules()))
        return 0
    rule = get_rule(rule_id)
    if rule is None:
        print(f"unknown rule: {rule_id!r}. Try --explain all.", file=sys.stderr)
        return 2
    print(f"{rule.rule_id} — {rule.summary}\n\n{rule.rationale}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    _load_rules()

    if args.explain:
        return _explain(args.explain)

    if not args.paths:
        print("error: no input files (try --help)", file=sys.stderr)
        return 2

    fail_on = Severity.from_name(args.fail_on)
    select = _split(args.select)
    ignore = _split(args.ignore)

    results = [
        analyze_path(path, data_days=args.data_days, select=select, ignore=ignore)
        for path in args.paths
    ]

    if args.json:
        print(render_json(results))
    else:
        color = (not args.no_color) and sys.stdout.isatty()
        print(render_text(results, color=color), end="")

    rc = 0
    for res in results:
        if any(f.rule_id != "rule-error" and f.severity >= fail_on for f in res.findings):
            rc = max(rc, 1)
        if res.error:
            rc = max(rc, 2)
    return rc


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
