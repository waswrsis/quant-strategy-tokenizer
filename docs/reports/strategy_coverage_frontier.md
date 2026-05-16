# QST Strategy Coverage Frontier

This is the PR 1 baseline and protocol report for Coverage Frontier v0.3. It is not a
final coverage frontier claim and does not publish a single strategy coverage percentage.

## Repo

- Branch: `main`
- Baseline HEAD before PR 1 docs: `9fd9a78aa4f6b9a58ed15531c42d26d4d9ffc9f0`
- Dirty state before PR 1 docs: clean
- Local branch state before PR 1 docs: ahead of `origin/main` by 1 commit

## Current Command Evidence

| Command | Exit code | Output summary |
| --- | ---: | --- |
| `git status --short` | 0 | no output; clean before PR 1 docs |
| `git rev-parse --abbrev-ref HEAD` | 0 | `main` |
| `git rev-parse HEAD` | 0 | `9fd9a78aa4f6b9a58ed15531c42d26d4d9ffc9f0` |
| `python -m qst.cli --help` | 0 | CLI exposes `vocabulary`, `validate`, `hash`, `canonicalize`, `write-json`, and `token` |
| `python -m qst.cli vocabulary --check` | 0 | `ok: true`; 6 packs; 120 tokens; zero diagnostics |
| `python -m pytest tests -q` | 0 | `441 passed` |
| `python -m pytest --cov=qst --cov-fail-under=85 -q` | 0 | `441 passed`; total code coverage `88.63%` |

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

## Baseline Coverage

No strategy coverage matrix exists in PR 1. These values are intentionally not reported as
frontier percentages.

| Metric | Value | Evidence |
| --- | ---: | --- |
| Intent routing | TBD | no strategy coverage matrix yet |
| Direct built-in GKR coverage | TBD | no strategy coverage matrix yet |
| Partial record coverage | TBD | no strategy coverage matrix yet |
| Custom-token route coverage | TBD | no strategy coverage matrix yet |
| Routable record coverage | TBD | no strategy coverage matrix yet |
| False-supported rate | TBD | protocol added; no matrix or review data yet |
| Kernel-gap count | TBD | protocol added; no matrix rows yet |

## Protocol Baseline

PR 1 adds protocol files only:

- `docs/coverage/coverage_taxonomy.md`
- `docs/coverage/market_weight_protocol.md`
- `docs/coverage/false_supported_protocol.md`
- `docs/coverage/custom_token_route_policy.md`
- `docs/coverage/kernel_gap_decision_protocol.md`

## Boundary Statement

This baseline measures the strategy record layer only. It does not claim broker, exchange,
live trading, HFT runtime, full backtest engine, production execution, profitability, or
portfolio optimizer coverage.

## Next Work

- PR 2: matrix v0 and stratified external benchmark seed.
- PR 3: matrix validator and coverage report tool.
- PR 4: original failure dogfood case.

