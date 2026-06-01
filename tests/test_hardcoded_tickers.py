from overfitlint.core.context import AnalysisContext
from overfitlint.rules.hardcoded_tickers import HardcodedTickersRule


def _run(src):
    return HardcodedTickersRule().check(AnalysisContext.from_source(src))


def test_flags_banned_list_as_critical():
    f = _run('BANNED_TICKERS = {"SNDK", "LITE", "HL", "WDC", "TER"}\n')
    assert f and f[0].severity.name == "CRITICAL"


def test_flags_three_unnamed_tickers_as_warning():
    f = _run('picks = ["AAPL", "MSFT", "NVDA"]\n')
    assert f and f[0].severity.name == "WARNING"


def test_date_gated_list_is_critical():
    f = _run('OOS_START = "2026-01-31"\nrecent = {"HL", "TER"}\n')
    assert f and f[0].severity.name == "CRITICAL"


def test_ignores_ohlc_columns():
    assert _run('cols = ["OPEN", "HIGH", "LOW", "CLOSE"]\n') == []


def test_ignores_two_plain_words():
    assert _run('flags = ["NA", "ID"]\n') == []
