# Original Failure Strategy Dogfood

This report records the PR 4 dogfood case for Coverage Frontier v0.3. It converts
the project background strategy into coverage evidence without claiming runtime
execution, broker/exchange integration, live trading, backtest fidelity, profitability,
or complete grid behavior.

## Source

- Source document: `docs/project_history/PROJECT_EXPERIENCE.md`
- Relevant English background:
  - "multi-asset mean-reversion system for cryptocurrencies"
  - "grid-like staged adding"
  - "short volatility or short gamma"
  - "BTC regime, Markov state, NO-TRADE gating"
  - "slot budget, market freeze, openOrders cache, CircuitBreaker"
  - "BTC/Symbol VWAP, BTC-neutral, entry vote, degraded mode, structured audit"

The source is project background material. This PR does not copy private trading
code and does not treat historical returns as product evidence.

## Classification

- Dogfood id: `dog_001_original_multi_asset_mean_reversion_grid`
- Expected classification: `partially_supported`
- Candidate GKR: `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml`
- Intent fixture: `tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.intent.yaml`

The classification is partial because QST can represent a record-layer shell for
panel selection, weights, caps, and slot counting, but cannot represent the complete
staged grid execution system or account/order feedback runtime.

## Expressible Record Layer

| Component | Candidate token |
| --- | --- |
| Panel mean-reversion score normalization | `panel.zscore` |
| Contrarian bottom-k selection | `panel.bottom_k` |
| Raw equal-long weight record | `selection.to_weights` |
| Per-symbol cap record | `weight.cap_per_symbol` |
| Entry slot count record | `state.accumulate` |

## Non-Expressible Components

- Staged grid add ladder.
- VWAP add optimizer.
- BTC-led regime or Markov state model.
- Position-liquidity collapse function.
- Live order lifecycle.
- Broker/exchange execution.
- Account-level PnL feedback runtime.

These are recorded as gaps, not silently downgraded into supported behavior.

## Validation Evidence

| Command | Exit code | Summary |
| --- | ---: | --- |
| `python -m qst.cli validate tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml` | 0 | Candidate partial GKR validates. |
| `python -m qst.cli hash tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml` | 0 | Hashes recorded below. |
| `python -m qst.cli canonicalize tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml --output .local_audit/original_failure_strategy_dogfood.canonical.json` | 0 | Canonical artifact generated locally and not committed. |

## Hash Evidence

| Hash | Value |
| --- | --- |
| `graph_hash` | `sha256:4efaf0f8b3d562c85f93a8ed65506d3c2b49efa1f9227ec7264b780ecb4df82e` |
| `param_hash` | `sha256:07ecc5baa7f4c8ec77dec2fdaaeb95d0b98444340891d9baa311616b2204b5d8` |
| `instance_hash` | `sha256:64cb286d01db4fd9245d5bc27f0b16dd0f4ae5b6500b97f43e5fa06d9d022a39` |

## Gaps

| Gap | Detail | Preferred route |
| --- | --- | --- |
| `recipe_gap` | Staged grid adding is strategy-specific recipe behavior. | Future recipe or custom token route. |
| `regime_model_gap` | BTC-led regime and Markov gating are not accepted built-in model surfaces. | Custom token route or future accepted regime token. |
| `runtime_feedback_gap` | Open orders, fills, account PnL feedback, and live lifecycle state require runtime/adapter support. | Out of scope for coverage frontier record layer. |

## Verdict

The MVP dogfood case is accepted as a `partially_supported` coverage case once the
candidate GKR validates, hash evidence is recorded, the coverage matrix validator
passes, and the generated coverage report lists this dogfood row separately. It
does not satisfy the future frontier publication dogfood target by itself; later
work must add the broader target set or record an explicit deferral rationale.
