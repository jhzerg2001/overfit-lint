from overfitlint.core.context import AnalysisContext
from overfitlint.rules.excessive_params import ExcessiveParamsRule


def _run(src, **kw):
    return ExcessiveParamsRule().check(AnalysisContext.from_source(src, **kw))


def _many_params(n):
    return "".join(f"p{i} = {i + 2}.5\n" for i in range(n))


def test_warns_above_threshold():
    f = _run(_many_params(20))
    assert f and f[0].severity.name in ("WARNING", "CRITICAL")


def test_critical_far_above_threshold():
    f = _run(_many_params(40))
    assert f and f[0].severity.name == "CRITICAL"


def test_clean_under_threshold():
    assert _run(_many_params(5)) == []


def test_data_days_ratio_escalates_even_under_count():
    f = _run(_many_params(10), data_days=100)
    assert f  # 10 params < 15, but 10 days/param < 20 triggers the ratio check


def test_counts_inline_threshold_constants():
    body = " and ".join(f"r.x{i} > {i + 2}.5" for i in range(18))
    f = _run(f"def f(r):\n    return {body}\n")
    assert f  # 18 inline gate thresholds exceed the default threshold of 15


def test_ignores_trivial_zero_one():
    assert _run("a = 0\nb = 1\nc = -1\nd = 0\n") == []
