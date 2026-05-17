# QST Strategy Coverage Frontier

This is the dogfood target set baseline and protocol report for Coverage Frontier v0.3.
It is not a final coverage frontier claim and does not publish a single strategy coverage
percentage.

## Repo

- Branch: `main`
- PR 1 baseline commit: `8a483dc469e2966ab0b315a3e284728b6a3378c9`
- PR 2 baseline commit: `d2d6b77060b99dba332da6ac2bd748397f6f9d7a`
- PR 3 baseline commit: `d451391561f9b605fccf3f509335b00375f20b02`
- PR 4 baseline commit: `6bb4f2e839be26eb7ba2725e90355fbf6fc047d2`
- PR 4 scope: original failure strategy dogfood MVP case
- Dogfood target scope: five-case dogfood publication-target evidence set
- PR 6 scope: Section 19 core rule token batch coverage evidence
- PR 7 scope: kernel gap review and beta numeric-gap retirement
- PR 8 scope: panel/factor/weight record token batch coverage evidence
- PR 9 scope: state/gate/risk record token batch coverage evidence
- PR 10 scope: custom-token route governance, cap enforcement, and stale-route cleanup
- Runtime, IR, hash, schema, CI, prompt, and public example behavior changes: none
- Token surface changes: PR6, PR8, and PR9 accepted reference-helper tokens only; no broad runtime execution

## Current Command Evidence

| Command | Exit code | Output summary |
| --- | ---: | --- |
| `git status --short` | 0 | PR10 construction edits present before final commit |
| `git rev-parse --abbrev-ref HEAD` | 0 | `main` |
| `git rev-parse HEAD` | 0 | `a7ab948` before PR10 commit |
| `python -m qst.cli --help` | 0 | CLI exposes `vocabulary`, `validate`, `hash`, `canonicalize`, `write-json`, and `token` |
| `python -m qst.cli vocabulary --check` | 0 | `ok: true`; 6 packs; 179 tokens; zero diagnostics |
| `python -m pytest tests -q` | 0 | `501 passed` |
| `python -m pytest --cov=qst --cov-fail-under=85 -q` | 0 | `501 passed`; total code coverage `88.89%` |
| `python tools/validate_strategy_coverage_matrix.py docs/reports/strategy_coverage_matrix.yaml` | 0 | validation `pass`; zero issues |
| `python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --check` | 0 | report check `pass`; zero issues |
| `python -m pytest tests/token_conformance -q` | 0 | `53 passed` |
| `python -m pytest tests/coverage_cases -q` | 0 | `44 passed` |
| `python -m pytest tests/custom_runtime -q` | 0 | `16 passed` |
| `python -m pytest tests/e2e/test_reference_custom_token_v04.py -q` | 0 | `4 passed` |
| `python -m qst.cli validate tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml` | 0 | PR4 dogfood candidate validates |
| `python -m qst.cli hash tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml` | 0 | PR4 dogfood hashes recorded |
| `python -m qst.cli canonicalize tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml --output .local_audit/original_failure_strategy_dogfood.canonical.json` | 0 | canonical artifact generated locally |
| `python -m qst.cli validate tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml` | 0 | dogfood target candidate validates |
| `python -m qst.cli validate tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml` | 0 | dogfood target candidate validates |
| `python -m qst.cli validate tests/coverage_cases/state_gate_risk/min_max_hold_gate.partial.gkr.yaml` | 0 | PR9 state/gate candidate validates |
| `python -m qst.cli validate tests/coverage_cases/state_gate_risk/stop_take_profit_records.partial.gkr.yaml` | 0 | PR9 risk record candidate validates |
| `python -m qst.cli validate tests/coverage_cases/state_gate_risk/rebalance_time_window_records.partial.gkr.yaml` | 0 | PR9 rebalance/time-window candidate validates |

## Coverage Evidence Files

- `docs/reports/strategy_coverage_matrix.yaml`
- `docs/reports/external_benchmark_sources.md`
- `docs/reports/strategy_coverage_report.md`
- `tests/coverage_cases/external/README.md`
- `tests/coverage_cases/external/external_benchmark_seed.yaml`
- `tools/validate_strategy_coverage_matrix.py`
- `tools/report_strategy_coverage.py`
- `docs/reports/original_failure_strategy_dogfood.md`
- `docs/reports/dogfood_target_set.md`
- `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.intent.yaml`
- `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml`
- `tests/coverage_cases/dogfood/single_asset_trend_following_fsm.intent.yaml`
- `tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml`
- `tests/coverage_cases/dogfood/cross_sectional_factor_panel.intent.yaml`
- `tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml`
- `tests/coverage_cases/dogfood/custom_ml_score_signal.intent.yaml`
- `tests/coverage_cases/dogfood/reserved_event_stream_orderbook.intent.yaml`
- `tests/coverage_cases/core_rule/*.partial.gkr.yaml`
- `tests/coverage_cases/core_rule/*.hashes.json`
- `tests/coverage_cases/panel_factor_weight/*.partial.gkr.yaml`
- `tests/coverage_cases/panel_factor_weight/*.hashes.json`
- `tests/coverage_cases/state_gate_risk/*.partial.gkr.yaml`
- `tests/coverage_cases/state_gate_risk/*.hashes.json`
- `docs/reports/kernel_gap_review.md`
- `docs/reports/custom_token_governance_review.md`
- `tests/coverage_cases/custom_token_governance/custom_token_routes.yaml`

PR 2 created the seed data. PR 3 adds validator/report tooling and a checked-in generated
report. PR 4 adds the first dogfood MVP case and candidate partial GKR. The dogfood
target set completes the five-case publication-target evidence set while keeping dogfood
excluded from headline frontier metrics. PR 6 adds core rule token batch candidate
records under `tests/coverage_cases/core_rule/` without changing public demo acceptance.
PR 7 reviews active kernel gaps and retires the stale beta-estimator numeric
determinism gap for `int_050_beta_neutral_signal`.
PR 8 adds panel/factor/weight candidate records and retires current inverse-vol,
sector-neutral rank, and beta-neutral signal record gaps where explicit metadata
and candidate evidence exist.
PR 9 adds state/gate/risk candidate records and retires current hold, stop,
drawdown, exposure, turnover, and rebalance-band record gaps while keeping
Calendar/EventStream, Distribution, optimizer solver, broker/exchange, and
runtime execution boundaries deferred.
PR 10 records custom-token route governance evidence, enforces route manifest
coverage for active custom rows, and retires the stale `int_040_net_normalize`
custom route now covered by `weight.normalize_net` record evidence.

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
| Total patterns | 120 | matrix v0 plus dogfood target set, PR6 core rule, PR8 panel/factor/weight, and PR9 state/gate/risk rows |
| Internal matrix rows | 95 | matrix v0 plus PR6, PR8, and PR9 internal evidence rows |
| External benchmark rows | 20 | matrix v0 plus `external_benchmark_sources.md` |
| Dogfood rows | 5 | MVP and publication-target dogfood set |
| Reserved plus non-goal rows | >= 10 | matrix v0 sanity check |
| External stratification | complete for PR 2 required categories | matrix v0 sanity check |
| Validator result | pass | `tools/validate_strategy_coverage_matrix.py` |
| Report check result | pass | `tools/report_strategy_coverage.py --check` |

PR6 registers eight core rule coverage rows:

- `int_020_macd_trend`
- `int_021_atr_filter`
- `int_022_linear_regression_slope`
- `int_081_signal_composition`
- `int_082_decision_long_short_rule`
- `int_083_entry_exit_gate_record`
- `int_084_beta_residual_timeseries`
- `int_085_donchian_volatility_rule`

The PR6 rows are record/reference evidence. They do not add broad runtime execution,
broker/exchange behavior, backtesting, optimizer execution, or profitability claims.

PR7 records kernel review evidence in `docs/reports/kernel_gap_review.md`.
PR7 changes `int_050_beta_neutral_signal` from custom-token route to partially
supported beta/residual record evidence. PR8 upgrades current beta-neutral
signal, sector-neutral rank, and inverse-vol weight rows to supported record
evidence where explicit metadata and candidate GKR files exist. EventStream,
OrderBook, Calendar, Distribution, optimizer solver determinism, FSM recipes,
and rebalance-band reducer semantics remain deferred.

PR8 registers eight panel/factor/weight coverage rows:

- `int_041_inverse_vol_weight`
- `int_049_sector_neutral_rank`
- `int_050_beta_neutral_signal`
- `int_086_panel_alias_records`
- `int_087_equal_rank_weight_records`
- `int_088_group_neutral_weight_record`
- `int_089_inverse_volatility_weight_record`
- `int_090_weight_vol_target_wrapper`

The PR8 rows are record/reference evidence. They do not add broad runtime
execution, broker/exchange behavior, backtesting, optimizer/rebalance execution,
or profitability claims.

PR9 registers fourteen state/gate/risk coverage rows:

- `int_027_min_hold_gate`
- `int_028_max_hold_gate`
- `int_029_trailing_stop_record`
- `int_030_stop_loss_record`
- `int_031_take_profit_record`
- `int_032_rebalance_band`
- `int_035_exposure_cap`
- `int_055_volatility_regime_gate`
- `int_056_drawdown_gate`
- `int_091_state_hold_gate_records`
- `int_092_stop_take_profit_risk_records`
- `int_093_trailing_drawdown_risk_records`
- `int_094_volatility_regime_time_window_records`
- `int_095_rebalance_exposure_turnover_records`

The PR9 rows are record/reference evidence. They do not add broker/exchange
execution, live stop orders, position lifecycle runtime, account feedback,
Calendar/EventStream TypeSpec, a rebalance scheduler, a backtest engine, or
profitability claims.

The PR 3 report tool now computes:

- intent routing by coverage class
- direct built-in record coverage
- partial record coverage
- custom-token route coverage using provisional discount `0.5`
- reserved/non-goal boundary count
- false-supported review queue
- kernel-gap review queue

The report still does not publish a single final coverage percentage because semantic
false-supported review is pending and dogfood evidence remains deliberately separated from
headline frontier metrics.

## Report Metrics

Current generated metrics from `docs/reports/strategy_coverage_report.md`:

| Metric | Value |
| --- | ---: |
| direct_builtin_coverage | 0.3733 |
| routable_record_coverage_raw | 0.8970 |
| routable_record_coverage_discounted | 0.8556 |
| custom_token_route_share | 0.0923 |
| false_supported_rate_mechanical | 0.0000 |
| false_supported_rate_semantic | 0.0000 |
| false_supported_rate_boundary | 0.0000 |
| boundary_false_supported_count | 0 |
| kernel_gap_count | 12 |
| token_bloat_index | 0.0522 |

## Custom Token Governance

PR10 adds `docs/reports/custom_token_governance_review.md` and the route manifest
at `tests/coverage_cases/custom_token_governance/custom_token_routes.yaml`.

Current governance status:

- active custom routes: 10
- missing governance rows: 0
- stale custom route findings: 0
- route cap: 0.40
- current custom_token_route_share: 0.0923

`indicator.kdj`, built-in Kalman signal, pair-spread model, score calibration,
and external model routes remain future token/governance candidates. PR10 does
not convert them into built-in tokens and does not execute, approve, or grant
custom code.

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

## Dogfood Target Set

The matrix includes five dogfood rows:

- `dog_001_original_multi_asset_mean_reversion_grid`
- `dog_002_single_asset_trend_following_fsm`
- `dog_003_cross_sectional_factor_panel`
- `dog_004_custom_ml_score_signal`
- `dog_005_reserved_event_stream_orderbook`

Artifacts:

- MVP report: `docs/reports/original_failure_strategy_dogfood.md`
- Target report: `docs/reports/dogfood_target_set.md`
- Intent fixtures: `tests/coverage_cases/dogfood/*.intent.yaml`
- Candidate GKR files for supported/partial dogfood rows:
  - `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml`
  - `tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml`
  - `tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml`

Classifications:

- `partially_supported`: original multi-asset grid, single-asset trend-following FSM,
  cross-sectional factor panel
- `custom_token_required`: custom ML score signal
- `reserved`: event-stream order-book strategy

Target status:

- MVP dogfood requirement `>=1`: pass
- Frontier publication target `>=5`: pass

Known gaps:

- staged grid add ladder, VWAP add optimizer, and BTC-led regime model
- full position FSM lifecycle and broker-side stop lifecycle
- factor construction governance, sector metadata, optimizer, and rebalance scheduler
- custom ML model implementation and approval/execution boundary
- EventStream, OrderBook, and event-time replay runtime

The supported/partial candidate GKR files validate and have hash/canonical command
evidence. Custom and reserved dogfood rows intentionally do not provide candidate GKR
files because their boundaries are custom-token governance and reserved-design runtime,
respectively.

## Protocol Baseline

PR 1 added protocol files:

- `docs/coverage/coverage_taxonomy.md`
- `docs/coverage/market_weight_protocol.md`
- `docs/coverage/false_supported_protocol.md`
- `docs/coverage/custom_token_route_policy.md`
- `docs/coverage/kernel_gap_decision_protocol.md`

PR 2 registers the first matrix and external seed against those protocols. PR 3 adds the
validator and report tool for the matrix. PR 4 wires the first original-failure dogfood
case into the matrix and report. The dogfood target set expands that evidence to five
cases. PR10 adds custom-token governance evidence and keeps the provisional custom route
discount/cap machine-checkable.

## Boundary Statement

This baseline measures the strategy record layer only. It does not claim broker, exchange,
live trading, HFT runtime, full backtest engine, production execution, profitability, or
portfolio optimizer coverage.

## Next Work

- Resume the planned Coverage Frontier sequence with prompt minimum alignment or the next
  token/kernel evidence PR. PR10 leaves `indicator.kdj` as the highest-efficiency
  next-best token candidate and leaves reserved/non-goal boundary hardening for the
  next planned stage.
