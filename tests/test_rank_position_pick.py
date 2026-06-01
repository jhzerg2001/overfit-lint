from overfitlint.core.context import AnalysisContext
from overfitlint.rules.rank_position_pick import RankPositionPickRule


def _run(src):
    return RankPositionPickRule().check(AnalysisContext.from_source(src))


def test_flags_named_rank_start_param():
    f = _run("rank_start = 15\n")
    assert f and f[0].severity.name == "CRITICAL"


def test_flags_iloc_mid_rank_as_critical():
    f = _run("basket = ranked.iloc[5]\n")
    assert f and f[0].severity.name == "CRITICAL"


def test_flags_score_index_three_as_warning():
    f = _run("pick = scores[2]\n")
    assert f and f[0].severity.name == "WARNING"


def test_flags_rank_equals_comparison():
    f = _run("keep = (rank == 6)\n")
    assert f and f[0].severity.name == "CRITICAL"


def test_flags_argsort_slice_skipping_head():
    f = _run("sel = argsort(-vals)[2:8]\n")
    assert f


def test_allows_top_one_and_two():
    assert _run("a = ranked.iloc[0]\nb = ranked.iloc[1]\n") == []


def test_allows_rank_param_one_or_two():
    assert _run("rank_start = 1\nrank_slot = 2\n") == []


def test_ignores_non_ranked_indexing():
    assert _run("x = data[5]\ny = weights[2]\n") == []
