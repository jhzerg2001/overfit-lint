# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-31

### Added
- Initial release.
- Seven overfitting-smell rules: `magic-thresholds`, `param-encoded-name`,
  `hardcoded-tickers`, `hardcoded-anchors`, `rank-position-pick`, `excessive-params`,
  `gate-stacking` — each with a one-line rationale and positive/negative test fixtures.
- CLI with text and JSON output, `--fail-on`, `--select`/`--ignore`, `--data-days`,
  `--explain`, and CI-friendly exit codes.
- A documented `0–100` smell score.
- `clean_momentum` and `overfit_example` reference strategies.
- Zero runtime dependencies (standard library only); supports Python 3.10–3.13.
