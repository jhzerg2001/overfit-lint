from overfitlint.core.context import AnalysisContext
from overfitlint.rules.hardcoded_anchors import HardcodedAnchorsRule


def _run(src):
    return HardcodedAnchorsRule().check(AnalysisContext.from_source(src))


def test_flags_reference_return_as_critical():
    f = _run("top1_reference_full_return_pct = 414.45\n")
    assert f and f[0].severity.name == "CRITICAL"


def test_flags_funnel_in_dict_as_critical():
    f = _run('cfg = {"FUNNEL_3_min_return": 85.0}\n')
    assert f and f[0].severity.name == "CRITICAL"


def test_warns_on_target_return_without_strong_name():
    f = _run("target_return = 0.45\n")
    assert f and f[0].severity.name == "WARNING"


def test_ignores_plain_numbers():
    assert _run("lookback = 21\nhold_days = 5\nweight = 0.5\n") == []
