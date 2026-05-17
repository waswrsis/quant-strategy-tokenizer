# QST Strategy Coverage Frontier

This is the PR 4 baseline and protocol report for Coverage Frontier v0.3. It is not a
final coverage frontier claim and does not publish a single strategy coverage percentage.

## Repo

- Branch: `main`
- PR 1 baseline commit: `8a483dc469e2966ab0b315a3e284728b6a3378c9`
- PR 2 baseline commit: `d2d6b77060b99dba332da6ac2bd748397f6f9d7a`
- PR 3 baseline commit: `d451391561f9b605fccf3f509335b00375f20b02`
- PR 4 scope: original failure strategy dogfood MVP case
- Runtime, token, IR, hash, schema, CI, prompt, and example behavior changes: none

## Current Command Evidence

| Command | Exit code | Output summary |
| --- | ---: | --- |
| `git status --short` | 0 | PR4 construction edits present before final commit |
| `git rev-parse --abbrev-ref HEAD` | 0 | `main` |
| `git rev-parse HEAD` | 0 | `d451391561f9b605fccf3f509335b00375f20b02` |
| `python -m qst.cli --help` | 0 | CLI exposes `vocabulary`, `validate`, `hash`, `canonicalize`, `write-json`, and `token` |
| `python -m qst.cli vocabulary --check` | 0 | `ok: true`; 6 packs; 120 tokens; zero diagnostics |
| `python -m pytest tests -q` | 0 | `460 passed` |
| `python -m pytest --cov=qst --cov-fail-under=85 -q` | 0 | `460 passed`; total code coverage `88.63%` |
| `python tools/validate_strategy_coverage_matrix.py docs/reports/strategy_coverage_matrix.yaml` | 0 | validation `pass`; zero issues |
| `python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --check` | 0 | report check `pass`; zero issues |
| `python -m qst.cli validate tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml` | 0 | PR4 dogfood candidate validates |
| `python -m qst.cli hash tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml` | 0 | PR4 dogfood hashes recorded |
| `python -m qst.cli canonicalize tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml --output .local_audit/original_failure_strategy_dogfood.canonical.json` | 0 | canonical artifact generated locally |

## Coverage Evidence Files

- `docs/reports/strategy_coverage_matrix.yaml`
- `docs/reports/external_benchmark_sources.md`
- `docs/reports/strategy_coverage_report.md`
- `tests/coverage_cases/external/README.md`
- `tests/coverage_cases/external/external_benchmark_seed.yaml`
- `tools/validate_strategy_coverage_matrix.py`
- `tools/report_strategy_coverage.py`
- `docs/reports/original_failure_strategy_dogfood.md`
- `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.intent.yaml`
- `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml`

PR 2 created the seed data. PR 3 adds validator/report tooling and a checked-in generated
report. PR 4 adds the first dogfood MVP case and candidate partial GKR.

## Existing Examples

Inventory command:

```powershell
Get-ChildItem -Recurse -File examples\strategies | Sort-Object FullName
```

Summary:

| Inventory | Count |
| --- | ---: |
| files under `examples/strategies` | 27 |
| `.gkr.yaml` strategy sources | 14 |
| public demo case directories | 12 |

Public demo cases:

| Case | Strategy file | Reference artifacts |
| --- | --- | --- |
| `01_ema_cross` | `examples/strategies/01_ema_cross/strategy.gkr.yaml` | diagnostics, fixture, hashes, trace |
| `02_rsi_reversal` | `examples/strategies/02_rsi_reversal/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `03_bollinger_mean_reversion` | `examples/strategies/03_bollinger_mean_reversion/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `04_breakout_channel` | `examples/strategies/04_breakout_channel/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `05_cooldown_trend_following` | `examples/strategies/05_cooldown_trend_following/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `06_circuit_breaker_mean_reversion` | `examples/strategies/06_circuit_breaker_mean_reversion/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `07_topk_momentum_panel` | `examples/strategies/07_topk_momentum_panel/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `08_market_neutral_rank` | `examples/strategies/08_market_neutral_rank/strategy.gkr.yaml` | diagnostics, fixture, hashes, trace |
| `09_btc_residual_meanrev` | `examples/strategies/09_btc_residual_meanrev/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `10_volatility_target_weight` | `examples/strategies/10_volatility_target_weight/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `11_turnover_constrained_rebalance` | `examples/strategies/11_turnover_constrained_rebalance/strategy.gkr.yaml` | diagnostics, fixture, hashes |
| `12_custom_token_kalman_signal` | `examples/strategies/12_custom_token_kalman_signal/strategy.gkr.yaml` | diagnostics, fixture, hashes, trace |

Additional standalone strategy sources:

- `examples/strategies/kdj_cross_basic.gkr.yaml`
- `examples/strategies/kdj_with_ema_filter.gkr.yaml`

## Reference Inventory

Inventory command:

```powershell
Get-ChildItem -Recurse -File tests\reference | Sort-Object FullName
```

Summary:

| Inventory | Count |
| --- | ---: |
| files under `tests/reference` | 88 |
| public strategy reference case directories | 12 |
| public full trace strategy cases | 3 |

Reference groups:

- `tests/reference/strategies`: public demo diagnostics, fixtures, hashes, and selected traces.
- `tests/reference/temporal`: temporal validation diagnostics and traces.
- `tests/reference/state`: state/gate fixtures, diagnostics, strategies, and traces.
- `tests/reference/panel`: panel fixtures, diagnostics, strategies, and traces.
- `tests/reference/custom_token`: custom token Kalman strategy, fixtures, diagnostics, and traces.

## Matrix Baseline

PR 2 adds matrix v0 with seed rows. PR 3 validates that matrix and generates
`docs/reports/strategy_coverage_report.md`. This is still not a final frontier percentage.

| Metric | Value | Evidence |
| --- | ---: | --- |
| Schema version | `qst-strategy-coverage/0.3` | `docs/reports/strategy_coverage_matrix.yaml` |
| Total patterns | 101 | matrix v0 |
| Internal matrix rows | 80 | matrix v0 |
| External benchmark rows | 20 | matrix v0 plus `external_benchmark_sources.md` |
| Dogfood rows | 1 | PR4 MVP dogfood case |
| Reserved plus non-goal rows | >= 10 | matrix v0 sanity check |
| External stratification | complete for PR 2 required categories | matrix v0 sanity check |
| Validator result | pass | `tools/validate_strategy_coverage_matrix.py` |
| Report check result | pass | `tools/report_strategy_coverage.py --check` |

The PR 3 report tool now computes:

- intent routing by coverage class
- direct built-in record coverage
- partial record coverage
- custom-token route coverage using provisional discount `0.5`
- reserved/non-goal boundary count
- false-supported review queue
- kernel-gap review queue

The report still does not publish a single final coverage percentage because semantic
false-supported review is pending and the full frontier publication dogfood target set is
not complete.

## Report Metrics

Current generated metrics from `docs/reports/strategy_coverage_report.md`:

| Metric | Value |
| --- | ---: |
| direct_builtin_coverage | 0.1412 |
| routable_record_coverage_raw | 0.8820 |
| routable_record_coverage_discounted | 0.8056 |
| custom_token_route_share | 0.1732 |
| false_supported_rate_mechanical | 0.0000 |
| false_supported_rate_semantic | 0.0000 |
| false_supported_rate_boundary | 0.0000 |
| boundary_false_supported_count | 0 |
| kernel_gap_count | 23 |
| token_bloat_index | 0.2200 |

## External Benchmark Seed

PR 2 adds `docs/reports/external_benchmark_sources.md` and
`tests/coverage_cases/external/external_benchmark_seed.yaml`.

The external seed covers at least one pattern for each required PR 2 category:

- `indicator_rule`
- `mean_reversion`
- `trend_following`
- `breakout`
- `state_gate`
- `panel_factor`
- `weight_record`
- `custom_signal`
- `custom_model`
- `reserved_event_stream`
- `non_goal_execution`

The seed records strategy intent and source references only. It is not an executable test
suite and does not copy proprietary strategy code.

## Dogfood MVP

The matrix includes one PR4 dogfood MVP row:

- `dog_001_original_multi_asset_mean_reversion_grid`

Artifacts:

- Report: `docs/reports/original_failure_strategy_dogfood.md`
- Intent fixture: `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.intent.yaml`
- Candidate GKR: `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml`

Classification:

- `partially_supported`

Expressible record shell:

- `panel.zscore`
- `panel.bottom_k`
- `selection.to_weights`
- `weight.cap_per_symbol`
- `state.accumulate`

Known gaps:

- staged grid add ladder
- VWAP add optimizer
- BTC-led regime or Markov model
- position-liquidity collapse function
- live order lifecycle, broker/exchange execution, and account-level feedback runtime

The candidate GKR validates and has hash/canonical command evidence, so the dogfood row
now satisfies the MVP `>=1 case` requirement. It still does not satisfy the future frontier
publication target by itself; later work must add the broader target set or record an
explicit deferral rationale.

## Protocol Baseline

PR 1 added protocol files:

- `docs/coverage/coverage_taxonomy.md`
- `docs/coverage/market_weight_protocol.md`
- `docs/coverage/false_supported_protocol.md`
- `docs/coverage/custom_token_route_policy.md`
- `docs/coverage/kernel_gap_decision_protocol.md`

PR 2 registers the first matrix and external seed against those protocols. PR 3 adds the
validator and report tool for the matrix. PR 4 wires the first original-failure dogfood
case into the matrix and report.

## Boundary Statement

This baseline measures the strategy record layer only. It does not claim broker, exchange,
live trading, HFT runtime, full backtest engine, production execution, profitability, or
portfolio optimizer coverage.

## Next Work

- PR 5 or follow-up: expand the dogfood target set or record an explicit frontier
  publication deferral rationale.
