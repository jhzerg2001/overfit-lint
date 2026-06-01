# Contributing to overfit-lint

Thanks for your interest! overfit-lint is a **heuristic** linter, so its value lives in a
low false-positive rate. Every rule change should come with tests — and the *negative*
tests (code that must **not** fire) matter most.

## Dev setup

```bash
git clone https://github.com/jhzerg2001/overfit-lint
cd overfit-lint
pip install -e ".[dev]"
pytest
```

## Adding a rule

1. Create `overfitlint/rules/<your_rule>.py` with a `Rule` subclass decorated with
   `@register`. Set `rule_id`, `summary`, and `rationale` (the rationale is shown to users
   via `--explain` and stored on each finding as `why`).
2. Import the module in `overfitlint/rules/__init__.py` so it registers.
3. Add `tests/test_<your_rule>.py` with:
   - **positive** fixtures — minimal snippets that *should* fire, at the expected severity;
   - **negative** fixtures — clean snippets that must stay silent.
4. Run `pytest` and make sure it is green.

Shared AST helpers live in `overfitlint/rules/_util.py`.

## Philosophy

- A rule should detect a tell that has **no good economic justification** — something you
  cannot defend with first-principles reasoning, only with "it backtested well".
- **Prefer a missed smell over a false alarm.** Noise kills a linter; a few confident
  findings beat a wall of maybes.
- Explain, don't just flag. Each finding's `why` should teach the reader *why* the pattern
  is a sign of overfitting.

## Scope

overfit-lint is intentionally small: single-file static analysis of Python strategy code,
zero runtime dependencies. Numerical tests (Deflated Sharpe, PBO, walk-forward) and
cross-variant analysis are out of scope by design — they belong in complementary tools.
