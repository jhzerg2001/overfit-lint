import pathlib

from overfitlint.core.runner import analyze_path

EXAMPLES = pathlib.Path(__file__).resolve().parent.parent / "examples"


def test_clean_example_has_no_warnings_or_criticals():
    res = analyze_path(str(EXAMPLES / "clean_momentum.py"))
    assert res.error is None
    bad = [f for f in res.findings if f.severity.name in ("WARNING", "CRITICAL")]
    assert bad == [], [f"{f.rule_id} L{f.line}: {f.message}" for f in bad]


def test_overfit_example_triggers_every_rule():
    res = analyze_path(str(EXAMPLES / "overfit_example.py"))
    assert res.error is None
    ids = {f.rule_id for f in res.findings}
    expected = {
        "magic-thresholds",
        "param-encoded-name",
        "hardcoded-tickers",
        "hardcoded-anchors",
        "rank-position-pick",
        "excessive-params",
        "gate-stacking",
    }
    assert expected <= ids, f"missing: {expected - ids}"
