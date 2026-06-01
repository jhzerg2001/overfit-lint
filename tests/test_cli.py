import json

import pytest

from overfitlint.cli import main


def test_version_prints_and_exits(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "overfit-lint" in capsys.readouterr().out


def test_clean_file_exit_zero(tmp_path, capsys):
    p = tmp_path / "clean.py"
    p.write_text("lookback = 21\nweight = 0.5\n")
    assert main([str(p)]) == 0
    assert "clean" in capsys.readouterr().out


def test_smelly_file_exit_one(tmp_path, capsys):
    p = tmp_path / "bad.py"
    p.write_text('BANNED = {"AAPL", "MSFT", "NVDA"}\nw = 0.3569571510008239\n')
    assert main([str(p)]) == 1
    assert "hardcoded-tickers" in capsys.readouterr().out


def test_json_output_is_valid(tmp_path, capsys):
    p = tmp_path / "bad.py"
    p.write_text("w = 0.3569571510008239\n")
    main(["--json", str(p)])
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list) and data[0]["findings"]
    assert data[0]["score"] > 0


def test_select_limits_rules(tmp_path, capsys):
    p = tmp_path / "bad.py"
    p.write_text('BANNED = {"AAPL", "MSFT", "NVDA"}\nw = 0.3569571510008239\n')
    main(["--select", "magic-thresholds", "--json", str(p)])
    data = json.loads(capsys.readouterr().out)
    ids = {f["rule_id"] for f in data[0]["findings"]}
    assert ids == {"magic-thresholds"}


def test_explain_prints_rationale(capsys):
    assert main(["--explain", "rank-position-pick"]) == 0
    assert "mid-rank" in capsys.readouterr().out


def test_explain_all_lists_rules(capsys):
    assert main(["--explain", "all"]) == 0
    out = capsys.readouterr().out
    assert "magic-thresholds" in out and "gate-stacking" in out


def test_missing_file_exit_two(capsys):
    assert main(["/no/such/file_xyz_overfit.py"]) == 2


def test_no_paths_exit_two(capsys):
    assert main([]) == 2
