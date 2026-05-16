# QST Strategy Coverage Frontier

This is the PR 2 baseline and protocol report for Coverage Frontier v0.3. It is not a
final coverage frontier claim and does not publish a single strategy coverage percentage.

## Repo

- Branch: `main`
- PR 1 baseline commit: `8a483dc469e2966ab0b315a3e284728b6a3378c9`
- PR 2 scope: matrix v0 and stratified external benchmark seed
- Runtime, token, IR, hash, schema, CI, prompt, and example behavior changes: none

## Current Command Evidence

| Command | Exit code | Output summary |
| --- | ---: | --- |
| `git status --short` | 0 | clean before PR 2 edits |
| `git rev-parse --abbrev-ref HEAD` | 0 | `main` |
| `git rev-parse HEAD` | 0 | `8a483dc469e2966ab0b315a3e284728b6a3378c9` |
| `python -m qst.cli --help` | 0 | CLI exposes `vocabulary`, `validate`, `hash`, `canonicalize`, `write-json`, and `token` |
| `python -m qst.cli vocabulary --check` | 0 | `ok: true`; 6 packs; 120 tokens; zero diagnostics |
| `python -m pytest tests -q` | 0 | `441 passed` |
| `python -m pytest --cov=qst --cov-fail-under=85 -q` | 0 | `441 passed`; total code coverage `88.63%` |

## PR 2 Evidence Files

- `docs/reports/strategy_coverage_matrix.yaml`
- `docs/reports/external_benchmark_sources.md`
- `tests/coverage_cases/external/README.md`
- `tests/coverage_cases/external/external_benchmark_seed.yaml`

These files create seed data only. PR 3 owns validator and report tooling.

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

PR 2 adds matrix v0 with seed rows, not a final frontier percentage.

| Metric | Value | Evidence |
| --- | ---: | --- |
| Schema version | `qst-strategy-coverage/0.3` | `docs/reports/strategy_coverage_matrix.yaml` |
| Total patterns | 101 | matrix v0 |
| Internal matrix rows | 80 | matrix v0 |
| External benchmark rows | 20 | matrix v0 plus `external_benchmark_sources.md` |
| Dogfood rows | 1 | provisional placeholder only |
| Reserved plus non-goal rows | >= 10 | matrix v0 sanity check |
| External stratification | complete for PR 2 required categories | matrix v0 sanity check |

The matrix can support these future PR 3 report metrics:

- intent routing by coverage class
- direct built-in record coverage
- partial record coverage
- custom-token route coverage using provisional discount `0.5`
- reserved/non-goal boundary count
- false-supported review queue
- kernel-gap review queue

The matrix does not yet publish a single coverage percentage because PR 3 has not added
the validator/report tool and semantic false-supported review is still pending.

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

## Dogfood Placeholder

The matrix includes one provisional dogfood row:

- `dog_001_original_multi_asset_mean_reversion_grid`

It exists only to wire the matrix for PR 3 and PR 4. It does not count as final frontier
publication evidence. PR 4 owns the detailed dogfood artifact, candidate GKR, diagnostics,
false-supported review, and final routing decision.

## Protocol Baseline

PR 1 added protocol files:

- `docs/coverage/coverage_taxonomy.md`
- `docs/coverage/market_weight_protocol.md`
- `docs/coverage/false_supported_protocol.md`
- `docs/coverage/custom_token_route_policy.md`
- `docs/coverage/kernel_gap_decision_protocol.md`

PR 2 registers the first matrix and external seed against those protocols.

## Boundary Statement

This baseline measures the strategy record layer only. It does not claim broker, exchange,
live trading, HFT runtime, full backtest engine, production execution, profitability, or
portfolio optimizer coverage.

## Next Work

- PR 3: matrix validator and coverage report tool.
- PR 4: original failure dogfood case.
