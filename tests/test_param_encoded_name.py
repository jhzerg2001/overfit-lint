from overfitlint.core.context import AnalysisContext
from overfitlint.rules.param_encoded_name import ParamEncodedNameRule


def _run(src):
    return ParamEncodedNameRule().check(AnalysisContext.from_source(src))


def test_flags_source_candidate_as_critical():
    f = _run('source_candidate = "Q_R7_VIX78"\n')
    assert any(x.severity.name == "CRITICAL" for x in f)


def test_flags_champion_name():
    f = _run("champion_config = 1\n")
    assert any("champion" in x.evidence.get("text", "") for x in f)


def test_flags_iter_inside_filename_string():
    f = _run('path = "best_v9_iter9_FINAL.json"\n')
    assert f


def test_ignores_plain_names():
    assert _run("momentum = compute(returns)\nlookback = 21\nweights = [0.5, 0.5]\n") == []
