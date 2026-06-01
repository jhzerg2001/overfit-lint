# overfit-lint

> Static analysis for the overfitting you *can't* see in a backtest.

![CI](https://github.com/jhzerg2001/overfit-lint/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**overfit-lint** reads quant-strategy *source code* — without running it — and flags the
fingerprints of an over-fitted research process: magic thresholds, search-encoded names,
hardcoded tickers and historical anchors, mid-rank cherry-picking, runaway free
parameters, and stacked gates.

```console
$ overfit-lint strategy.py
  L19 [critical] magic-thresholds: float literal 0.3569571510008239 carries 16 significant digits
  L22 [critical] hardcoded-tickers: hardcoded ticker list (5): SNDK, LITE, HL, WDC, TER
  L25 [critical] rank-position-pick: parameter 'rank_start' = 15 selects a fixed mid-rank (skips the top 14)
  L34 [warning]  gate-stacking: function 'eligible' stacks 9 numeric threshold gates
  ------------------------------------------------
  22 findings (8 critical, 4 warning, 10 info) — smell score 100/100
```

## Why another overfitting tool?

Most anti-overfitting tools are **numerical** — Deflated Sharpe, PBO, walk-forward. They
test one strategy for *in-sample information leakage*, and a careful strategy passes them.

But a whole class of overfitting never shows up in those numbers. It only shows up in the
**code**:

- a weight tuned to 16 decimal places (`0.3569571510008239`)
- a parameter named `Q_R7_VIX78` or `best_v9_iter9` — it won a grid search
- a 2026 ticker blacklist, or a single hardcoded `AAPL` anchor
- selecting the **6th**-ranked name instead of the 1st
- a `FUNNEL` gate requiring "≥ 85% return in 2024"
- 23 free parameters on 300 days of data

These are *answer-copying*: known history written back into the code. overfit-lint catches
them by reading the source, as a **complement** to numerical tests — they watch for
in-sample leakage, this watches for the logic- and process-level overfitting they miss.

## Install

A PyPI release (`pip install overfit-lint`) is planned. For now, install from source:

```bash
pip install git+https://github.com/jhzerg2001/overfit-lint
# or
git clone https://github.com/jhzerg2001/overfit-lint
cd overfit-lint
pip install -e .
```

No runtime dependencies — just the Python standard library (3.10+).

## Usage

```bash
overfit-lint strategy.py                 # scan a file
overfit-lint strategies/*.py             # scan many
overfit-lint strategy.py --json          # machine-readable
overfit-lint strategy.py --data-days 300 # also check params-per-data-day
overfit-lint strategy.py --fail-on critical   # CI gate
overfit-lint --explain rank-position-pick     # learn a rule
overfit-lint --explain all                    # list every rule
```

Exit codes: `0` clean · `1` findings at/above `--fail-on` (default `warning`) · `2` usage
or file error.

## The checks

| Rule | What it catches |
|---|---|
| `magic-thresholds` | Suspiciously precise float thresholds / weights (e.g. 16-decimal weights). |
| `param-encoded-name` | Names that encode grid-search provenance (`Q_R7_VIX78`, `iter9`, `champion`). |
| `hardcoded-tickers` | Hardcoded symbol lists — blacklists, OOS exclusions, single-name anchors. |
| `rank-position-pick` | Systematically picking a fixed mid-rank (the 6th, the 15th), skipping the top. |
| `excessive-params` | Too many free numeric parameters for the data on hand. |
| `gate-stacking` | A single decision path stacking many tuned threshold gates. |
| `hardcoded-anchors` | Performance targets / `FUNNEL` acceptance gates copied from known history. |

Every finding carries a one-line **`why`** explaining the tell — run with `--explain <rule>`
for the full rationale.

## Smell score

A single `0–100` score summarises a file, weighting findings by severity
(`info=1`, `warning=3`, `critical=8`):

```
score = min(100, round(100 * (1 - exp(-weighted / 12))))
```

Monotonic and saturating; `0` when clean. The constant is documented, not hidden — it would
be ironic for this tool to ship a magic number.

## In CI

```yaml
- run: pip install git+https://github.com/jhzerg2001/overfit-lint
- run: overfit-lint strategies/ --fail-on critical
```

## Programmatic API

```python
from overfitlint import analyze_path, smell_score

result = analyze_path("strategy.py", data_days=300)
for f in result.findings:
    print(f.rule_id, f.line, f.message)
print("score:", smell_score(result.findings))
```

## Limitations (read this)

overfit-lint is a **heuristic** linter, not a verdict. It reports *risk*, not proof:

- It can miss overfitting (a clean-looking file can still be over-fitted), and it can flag
  innocent code. Treat findings as questions to answer, not crimes.
- It does **not** run your strategy, compute returns, or do numerical tests — pair it with
  Deflated Sharpe / PBO / walk-forward, which cover what static analysis cannot.
- It analyses one Python file at a time. Cross-variant "survivor of a grid search" bias —
  the deepest form of overfitting — is by definition not visible in a single file.

See [`examples/`](examples/) for a clean strategy (scores 0) and a synthetic over-fitted
one (scores 100).

## Contributing

A rule is only as good as its false-positive rate. New rules need positive **and** negative
fixtures — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
