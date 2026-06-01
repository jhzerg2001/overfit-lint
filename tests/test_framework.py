"""Smoke tests for the core framework (no real rules involved)."""
from __future__ import annotations

import ast

from overfitlint.core.context import AnalysisContext
from overfitlint.core.finding import Finding, Severity
from overfitlint.core.report import render_json, render_text, smell_score
from overfitlint.core.rule import Rule
from overfitlint.core.runner import analyze_source


def test_context_parses_source():
    ctx = AnalysisContext.from_source("x = 1\n", path="t.py")
    assert isinstance(ctx.tree, ast.Module)
    assert ctx.lines == ["x = 1"]
    assert ctx.snippet(1) == "x = 1"
    assert ctx.snippet(999) == ""


def test_analyze_with_no_rules_is_clean():
    res = analyze_source("x = 1\n", rules=[])
    assert res.error is None
    assert res.findings == []


def test_syntax_error_is_reported_not_raised():
    res = analyze_source("def (:\n", rules=[])
    assert res.error is not None
    assert "syntax error" in res.error
    assert res.findings == []


class _AlwaysHits(Rule):
    rule_id = "always"

    def check(self, ctx):
        return [Finding("always", Severity.WARNING, "always hits", 1, snippet="x")]


class _Boom(Rule):
    rule_id = "boom"

    def check(self, ctx):
        raise RuntimeError("kaboom")


def test_custom_rule_runs():
    res = analyze_source("y = 2\n", rules=[_AlwaysHits()])
    assert [f.rule_id for f in res.findings] == ["always"]


def test_select_and_ignore_filters():
    rules = [_AlwaysHits()]
    assert analyze_source("y=2\n", rules=rules, select={"nope"}).findings == []
    assert analyze_source("y=2\n", rules=rules, ignore={"always"}).findings == []


def test_rule_exception_is_isolated():
    res = analyze_source("z = 3\n", rules=[_Boom(), _AlwaysHits()])
    ids = {f.rule_id for f in res.findings}
    assert "rule-error" in ids  # boom was caught
    assert "always" in ids      # and the other rule still ran


def test_smell_score_is_monotonic_and_bounded():
    assert smell_score([]) == 0
    one_info = [Finding("a", Severity.INFO, "m", 1)]
    many_crit = [Finding("a", Severity.CRITICAL, "m", i) for i in range(8)]
    assert 0 < smell_score(one_info) < smell_score(many_crit) <= 100


def test_rule_error_does_not_inflate_score():
    err = [Finding("rule-error", Severity.INFO, "boom", 0)]
    assert smell_score(err) == 0


def test_render_text_and_json_smoke():
    res = analyze_source("y = 2\n", rules=[_AlwaysHits()])
    txt = render_text([res])
    assert "always" in txt and "smell score" in txt
    js = render_json([res])
    assert '"rule_id": "always"' in js

    clean = analyze_source("y = 2\n", rules=[])
    assert "clean" in render_text([clean])
