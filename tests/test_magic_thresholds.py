from overfitlint.core.context import AnalysisContext
from overfitlint.rules.magic_thresholds import MagicThresholdsRule


def _run(src):
    return MagicThresholdsRule().check(AnalysisContext.from_source(src))


def test_flags_16_decimal_weight_as_critical():
    f = _run("w = 0.3569571510008239\n")
    assert len(f) == 1
    assert f[0].severity.name == "CRITICAL"


def test_flags_six_sig_as_warning():
    f = _run("x = 0.123457\n")
    assert len(f) == 1 and f[0].severity.name == "WARNING"


def test_flags_moderate_precision_as_info():
    f = _run("thr = 0.0857\n")
    assert len(f) == 1 and f[0].severity.name == "INFO"


def test_ignores_clean_round_floats():
    assert _run("a = 0.5\nb = 0.1\nc = 2.0\nd = 20.0\ne = 0.25\nf = 0.05\n") == []


def test_ignores_integers():
    assert _run("n = 100\nk = 3\nbig = 4000000000\n") == []
