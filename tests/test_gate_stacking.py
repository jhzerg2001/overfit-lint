from overfitlint.core.context import AnalysisContext
from overfitlint.rules.gate_stacking import GateStackingRule


def _run(src):
    return GateStackingRule().check(AnalysisContext.from_source(src))


def _gated_fn(n):
    conds = " and ".join(f"x{i} > {i + 2}" for i in range(n))
    return f"def eligible(row):\n    return {conds}\n"


def test_warns_when_many_gates():
    f = _run(_gated_fn(10))
    assert f and f[0].severity.name in ("WARNING", "CRITICAL")


def test_clean_when_few_gates():
    assert _run(_gated_fn(3)) == []


def test_ignores_len_and_range_bounds():
    src = (
        "def f(xs):\n"
        "    for i in range(len(xs)):\n"
        "        if i < len(xs):\n"
        "            pass\n"
    )
    assert _run(src) == []
