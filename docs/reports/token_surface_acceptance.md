# Token Surface Acceptance

Stage 3B accepts the token surface as registry-driven evidence, not a hand-written token list.
PR6 extends the accepted record/reference token surface with the core rule token batch.

## Baseline

- Stage 3A baseline commit: `14099e8154423e1d0b6bc639a1211b13f0a87ece`
- Baseline tag: `stage-3a-token-surface-complete-20260516`
- PR6 scope: Section 19 core rule token batch
- Built-in TokenPacks: `6`
- Built-in tokens: `150`
- Registry result: `ok`

## Pack Summary

| Pack | Version | Tokens | TokenPack Hash |
|---|---:|---:|---|
| qst-tokenpack-core-surface | 0.1.0 | 126 | `sha256:6ff7ff143b94e903a407f5599e7fee979af8f68d0d555ac7f25951b0ea0c396f` |
| qst-tokenpack-decision-algebra | 0.1.0 | 7 | `sha256:01e109dc96ef027fabff5fa8bcac8d8773e5c2a257462add3fb6050ba85c2794` |
| qst-tokenpack-panel-ops | 0.1.0 | 10 | `sha256:2b555101b1f2aa0e891f0b0657e99df2a3cc0ecb5314a204dac3169e494466b4` |
| qst-tokenpack-panel-weights | 0.1.0 | 3 | `sha256:5328a726a59d4204cdaa29996c436f212188a984b78b3f1bd36c17c4c67d6cf0` |
| qst-tokenpack-state-basic | 0.1.0 | 3 | `sha256:1b977f91c930b2f4daee489b0c6435d3d82a18d7132fd6aa00c8b979c4bda921` |
| qst-tokenpack-state-fsm | 0.1.0 | 1 | `sha256:9efa0c73ead4a5e8daa760ae6082e3851e2221c86690ebb330aa73edf3f88247` |

## Family Counts

- `align`: 4
- `bool`: 10
- `compare`: 13
- `continuous_score`: 2
- `data`: 5
- `decision`: 15
- `distribution`: 3
- `event`: 3
- `execution`: 5
- `gate`: 5
- `indicator`: 16
- `math`: 21
- `optimizer`: 1
- `panel`: 9
- `risk`: 3
- `signal`: 19
- `state`: 4
- `time`: 1
- `weight`: 4
- `window`: 7

## Maturity Counts

- `accepted`: 139
- `experimental`: 2
- `reserved_design`: 9

## Execution Support Counts

- `metadata_only`: 13
- `reference_helper`: 137

## Inventory

| TokenRef | Pack | Family | Layer | Maturity | Execution Support | Contract Scope | Determinism | Status |
|---|---|---|---|---|---|---|---|---|
| core.align.drop_missing | qst-tokenpack-core-surface | align | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.align.forward_fill | qst-tokenpack-core-surface | align | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.align.inner_join | qst-tokenpack-core-surface | align | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.align.left_join | qst-tokenpack-core-surface | align | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.bool.all | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.bool.and | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.bool.any | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.bool.count_true | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.bool.not | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.bool.or | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.bool.xor | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.between | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.eq | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.gt | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.gte | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.lt | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.lte | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.ne | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.cmp.outside | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.compare.eq | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.compare.ge | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.compare.gt | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.compare.le | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.compare.lt | qst-tokenpack-core-surface | compare | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.data.diff | qst-tokenpack-core-surface | data | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.data.identity | qst-tokenpack-core-surface | data | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.data.log_return | qst-tokenpack-core-surface | data | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.data.pct_change | qst-tokenpack-core-surface | data | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.data.shift | qst-tokenpack-core-surface | data | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.decision.entry_exit_to_position | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.gate_decision | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.lift_bool | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.long_flat | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.long_short | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.rank_to_selection | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.selection_to_weight | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.signal_to_decision | qst-tokenpack-core-surface | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.distribution.normal_fit | qst-tokenpack-core-surface | distribution | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.distribution.quantile | qst-tokenpack-core-surface | distribution | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.distribution.tail_probability | qst-tokenpack-core-surface | distribution | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.event.filter | qst-tokenpack-core-surface | event | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.event.join_asof | qst-tokenpack-core-surface | event | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.event.window_count | qst-tokenpack-core-surface | event | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.execution.cancel_order | qst-tokenpack-core-surface | execution | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.execution.fill_report | qst-tokenpack-core-surface | execution | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.execution.submit_order | qst-tokenpack-core-surface | execution | derived | reserved_design | metadata_only | validation_only | reserved | accepted |
| core.gate.circuit_breaker | qst-tokenpack-core-surface | gate | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.gate.cooldown | qst-tokenpack-core-surface | gate | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.gate.market_freeze | qst-tokenpack-core-surface | gate | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.gate.observe_period | qst-tokenpack-core-surface | gate | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.gate.slot_budget | qst-tokenpack-core-surface | gate | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.indicator.atr | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.beta | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.bollinger | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.bollinger_band | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.channel_breakout | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.indicator.donchian_channel | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.ema | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.linear_regression_slope | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.macd | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.residual | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.rolling_mean | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.rolling_std | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.rolling_zscore | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.rsi | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.sma | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.indicator.volatility | qst-tokenpack-core-surface | indicator | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.logic.and | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.logic.not | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.logic.or | qst-tokenpack-core-surface | bool | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.math.abs | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.add | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.ceil | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.clip | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.div | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.exp | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.fill_nan | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.floor | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.isfinite | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.math.isnan | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.math.log | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.max | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.min | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.mul | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.neg | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.pow | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.round | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.sign | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.sqrt | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.sub | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.math.where | qst-tokenpack-core-surface | math | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.norm.range_position | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.optimizer.mean_variance | qst-tokenpack-core-surface | optimizer | derived | experimental | metadata_only | validation_only | annotation_only | accepted |
| core.plan.noop | qst-tokenpack-core-surface | execution | derived | accepted | metadata_only | validation_only | annotation_only | accepted |
| core.plan.order_intent | qst-tokenpack-core-surface | execution | derived | accepted | metadata_only | validation_only | annotation_only | accepted |
| core.risk.position_cap | qst-tokenpack-core-surface | risk | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.risk.turnover_cap | qst-tokenpack-core-surface | risk | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.risk.volatility_target | qst-tokenpack-core-surface | risk | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.score.calibrate | qst-tokenpack-core-surface | continuous_score | derived | experimental | metadata_only | validation_only | annotation_only | accepted |
| core.score.zscore | qst-tokenpack-core-surface | continuous_score | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.signal.and | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.between | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.breakout_down | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.breakout_up | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.cross_above | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.cross_below | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.crosses | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.greater_than | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.less_than | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.not | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.or | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.outside_band | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.rank_bottom_k | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.rank_top_k | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.threshold_above | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.threshold_below | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.signal.zscore_revert | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.smooth.linear_recursive | qst-tokenpack-core-surface | signal | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.time.session_filter | qst-tokenpack-core-surface | time | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.window.count | qst-tokenpack-core-surface | window | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.window.max | qst-tokenpack-core-surface | window | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.window.mean | qst-tokenpack-core-surface | window | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.window.min | qst-tokenpack-core-surface | window | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.window.std | qst-tokenpack-core-surface | window | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.window.sum | qst-tokenpack-core-surface | window | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.window.zscore | qst-tokenpack-core-surface | window | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.decision.any_accept | qst-tokenpack-decision-algebra | decision | primitive | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.majority | qst-tokenpack-decision-algebra | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.permissive_and | qst-tokenpack-decision-algebra | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.quorum | qst-tokenpack-decision-algebra | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.strict_and | qst-tokenpack-decision-algebra | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.unknown_propagating_and | qst-tokenpack-decision-algebra | decision | primitive | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.decision.weighted_vote | qst-tokenpack-decision-algebra | decision | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.panel.bottom_k | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.panel.demean | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.panel.group_demean | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.panel.mask | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.panel.rank | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.panel.residualize | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.panel.top_k | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.panel.winsorize | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.panel.zscore | qst-tokenpack-panel-ops | panel | derived | accepted | reference_helper | reference_semantics | semantic_float64 | accepted |
| core.selection.to_weights | qst-tokenpack-panel-ops | weight | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.weight.cap_per_symbol | qst-tokenpack-panel-weights | weight | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.weight.market_neutral | qst-tokenpack-panel-weights | weight | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.weight.normalize_gross | qst-tokenpack-panel-weights | weight | derived | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.state.accumulate | qst-tokenpack-state-basic | state | primitive | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.state.delay | qst-tokenpack-state-basic | state | primitive | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.state.edge_detect | qst-tokenpack-state-basic | state | primitive | accepted | reference_helper | reference_semantics | reference_exact | accepted |
| core.state.fsm | qst-tokenpack-state-fsm | state | primitive | accepted | reference_helper | reference_semantics | reference_exact | accepted |

## Decision

All built-in tokens are present in deterministic registry order and carry `surface`, `contract`, `maturity`, `execution_support`, and deterministic capability metadata. Reserved-design tokens are accepted as vocabulary-visible boundaries only. PR6 additions are accepted reference-helper tokens only and do not imply broad runtime execution.
