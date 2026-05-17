# Kernel Gap Review

Coverage Frontier PR7 reviewed repeated kernel gaps after the PR6 core rule
token batch. PR8 updates this review for the panel/factor/weight batch and
retires the stale sector-neutral panel metadata gap where explicit GroupSpec
metadata is now provided by candidate coverage records. PR9 updates the review
for state/gate/risk records and retires stale FSM/reducer gaps now covered by
accepted record helpers. This report is evidence for deferral and low-risk
matrix fixes. It does not implement EventStream, Calendar, Distribution,
optimizer solver execution, broker or exchange execution, live runtime feedback,
a backtest engine, or new IR/hash semantics.

## Decision Summary

| Gap category | Active rows | Active weight | Decision | Preferred next stage |
| --- | ---: | ---: | --- | --- |
| `port_temporal_type_gap` | 7 | 27 | Defer | Extended TypeSpec / reserved boundary review |
| `fsm_state_gap` | 0 | 0 | Retired in PR9 for current matrix | Accepted state/gate/risk record helpers |
| `numeric_determinism_gap` | 5 | 20 | Partially fixed, then defer | Distribution and optimizer solver contracts |
| `panel_type_gap` | 0 | 0 | Retired in PR8 for current matrix | Explicit group metadata evidence |
| `reducer_semantics_gap` | 0 | 0 | Retired in PR9 for current matrix | Rebalance-band record helper evidence |

## PR7 Fix

PR6 accepted `indicator.beta` and `indicator.residual` reference helpers. That
retires the stale beta-estimator `numeric_determinism_gap` on
`int_050_beta_neutral_signal`.

PR7 updates that row from `custom_token_required` to `partially_supported` with
evidence from:

- `tests/coverage_cases/core_rule/beta_residual_timeseries.partial.gkr.yaml`
- `tests/coverage_cases/core_rule/beta_residual_timeseries.hashes.json`

The remaining gap is a beta-neutral signal recipe, not beta estimator
determinism. This is still partial record-layer coverage only; it does not claim
full beta-neutral portfolio construction, optimizer execution, rebalance
scheduling, broker routing, or live execution.

## PR8 Fix

PR8 accepts explicit panel/factor/weight reference-helper records:

- `factor.sector_neutral_rank` with required explicit group metadata;
- `factor.beta_neutral_signal` as residualized/beta-aware signal evidence;
- deterministic weight records such as `weight.inverse_vol_weight`,
  `weight.group_neutral_weight`, and `weight.normalize_net`.

This retires the active `panel_type_gap` on `int_049_sector_neutral_rank`
because the candidate GKR records provide explicit group metadata and do not
infer sector classifications. PR8 also upgrades `int_050_beta_neutral_signal`
from partial beta/residual evidence to supported factor signal evidence while
preserving the boundary that it is not a complete beta-neutral portfolio engine.

## PR9 Fix

PR9 accepts state/gate/risk reference-helper records for hold gates,
stop/take-profit records, trailing stops, drawdown and volatility-regime gates,
rebalance-band records, exposure caps, volatility-target aliases, and turnover
limits.

This retires current `fsm_state_gap` rows for minimum hold, maximum hold,
trailing stop, drawdown gate, and external trailing-stop evidence. PR9 also
retires the current `reducer_semantics_gap` on `int_032_rebalance_band` with
explicit `gate.rebalance` and `risk.turnover_limit_record` evidence.

The resulting coverage remains record-layer evidence only. It does not add live
stop orders, position lifecycle runtime, a rebalance scheduler, Calendar
TypeSpec, EventStream, broker/exchange execution, account runtime, or
backtesting.

## Deferred Kernel Gaps

### `port_temporal_type_gap`

Affected rows include calendar, EventStream, order-book, and HFT-like records.
These require temporal/type-system work or explicit reserved-boundary handling.
PR7 defers this category because implementing it would alter type/runtime
boundaries rather than simply retiring stale evidence.

### `fsm_state_gap`

No active matrix row currently carries `fsm_state_gap` after PR9. Future
stateful recipes must still separate record-layer state evidence from live order
lifecycle, fills, account feedback, and execution runtime.

### `numeric_determinism_gap`

After the beta fix, remaining rows are Distribution or optimizer solver
boundaries:

- `optimizer.mean_variance` solver determinism
- `distribution.normal_fit`
- `distribution.quantile`
- external Distribution VaR
- external portfolio optimizer

These remain deferred. Distribution TypeSpec/runtime and optimizer solver
contracts are not PR7 scope.

### `panel_type_gap`

No active matrix row currently carries `panel_type_gap` after PR8. Future
sector or instrument metadata work must still require explicit metadata; QST
must not infer sector membership or instrument classifications from symbol text.

### `reducer_semantics_gap`

No active matrix row currently carries `reducer_semantics_gap` after PR9.
Future reducer recipes must still be explicit record semantics and must not hide
rebalance scheduling, order routing, or optimizer behavior inside an existing
token.

## Acceptance

- All active kernel gap categories are reviewed.
- `int_050_beta_neutral_signal` no longer carries the stale beta-estimator
  `numeric_determinism_gap`.
- `int_049_sector_neutral_rank` no longer carries `panel_type_gap` because PR8
  candidate evidence supplies explicit group metadata.
- PR9 hold, stop, drawdown, and rebalance-band rows no longer carry stale
  `fsm_state_gap` or `reducer_semantics_gap` entries.
- Remaining `numeric_determinism_gap` records are Distribution or optimizer
  solver deferrals only.
- No QST runtime, IR, canonical/hash, schema, broker/exchange, or public demo
  behavior changes are part of PR7.
