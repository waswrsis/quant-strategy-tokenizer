# Token Gap Report

Stage 3B classifies coverage gaps so the next stage does not blindly add vocabulary. EventStream, Distribution, optimizer, and execution boundaries are explicitly not ordinary token gaps.

## Classified Gaps

| Priority | Gap Type | Gap | Evidence | Recommended Next Step |
|---|---|---|---|---|
| P1 | Derived/Recipe Gap | trailing stop | Current state/window/decision primitives can express it but no canonical recipe exists. | Strategy Pattern Demonstrations or recipe surface. |
| P1 | Derived/Recipe Gap | rebalance band | Needs a canonical composition, not a new primitive type. | Strategy Pattern Demonstrations. |
| P1 | Type Gap | EventStream[T] | event.* is correctly reserved; no EventStream TypeSpec/runtime exists. | Extended TypeSpec if event-driven use cases become priority. |
| P1 | Type Gap | Distribution[T] | distribution.* is correctly reserved; no Distribution TypeSpec/runtime exists. | Extended TypeSpec if probabilistic workflows become priority. |
| P1 | Data Model Gap | Instrument metadata | Instrument/calendar/corporate-action metadata is outside current TypeSpec. | Data model or Extended TypeSpec stage. |
| P2 | Runtime Gap | optimizer solver execution | optimizer.mean_variance has no deterministic solver contract. | Keep experimental until solver contract exists. |
| P2 | Runtime Gap | portfolio rebalance engine | Risk/weight helpers are deterministic transforms, not a portfolio engine. | Out of Stage 3B; possible integration stage. |
| P2 | External Boundary Gap | execution feedback | execution.* is a reserved adapter boundary. | Adapter contract stage, not token patch. |
| Non-goal | Non-goal | broker live execution loop | Live broker orchestration is not QST core. | Do not implement in token surface. |
| Non-goal | Non-goal | hidden parameter mutation | QST requires canonical/hash-visible parameters. | Do not support. |

## Decision

No P0 gap blocks the accepted Stage 3A token surface. P1 gaps cluster around authoring patterns and recipe demonstrations; deeper gaps are TypeSpec/data-model/runtime boundaries and should not be solved by adding metadata-only tokens.

## Retired Gaps

| Gap | Retired by | Evidence |
|---|---|---|
| `indicator.macd` | PR6 core rule token batch | `tests/coverage_cases/core_rule/macd_trend.partial.gkr.yaml` |
| beta estimator determinism for `int_050_beta_neutral_signal` | PR7 kernel gap review | `tests/coverage_cases/core_rule/beta_residual_timeseries.partial.gkr.yaml` |
| `weight.inverse_vol` convenience gap | PR8 panel/factor/weight batch | `tests/coverage_cases/panel_factor_weight/inverse_vol_weight.partial.gkr.yaml` |
| sector-neutral rank metadata gap | PR8 panel/factor/weight batch | `tests/coverage_cases/panel_factor_weight/sector_neutral_rank.partial.gkr.yaml` |
