# Token Contract Audit

Stage 3B audits whether token contracts are sufficient for validation, hashing, conformance tests, and agent reasoning.

## Acceptance Rules

- Accepted tokens must declare temporal, numeric, missing-data, and failure-mode contracts.
- Stateful tokens must declare state semantics.
- Panel-aware tokens must declare panel semantics.
- Solver-backed tokens cannot be accepted unless a solver determinism contract exists.
- Reserved-design tokens are valid only as `validation_only` / `metadata_only` boundaries.

## Pass

| TokenRef | Family | Maturity | Scope | Temporal | Numeric | Missing Data | Failure Mode |
|---|---|---|---|---|---|---|---|
| core.align.drop_missing | align | accepted | reference_semantics | declared_by_ports | semantic_float64 | drops None values from active timestamp set | diagnostic_error |
| core.align.forward_fill | align | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.align.inner_join | align | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.align.left_join | align | accepted | reference_semantics | declared_by_ports | semantic_float64 | right side may be None where timestamp is absent | diagnostic_error |
| core.bool.all | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | empty input emits diagnostic error unless allow_empty=true |
| core.bool.and | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.bool.any | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | empty input emits diagnostic error unless allow_empty=true |
| core.bool.count_true | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | empty input emits diagnostic error unless allow_empty=true |
| core.bool.not | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.bool.or | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.bool.xor | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.cmp.between | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | lower greater than upper emits diagnostic error |
| core.cmp.eq | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.cmp.gt | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.cmp.gte | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.cmp.lt | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.cmp.lte | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.cmp.ne | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.cmp.outside | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | lower greater than upper emits diagnostic error |
| core.compare.eq | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.compare.ge | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.compare.gt | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.compare.le | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.compare.lt | compare | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.data.diff | data | accepted | reference_semantics | uses previous timestamp only | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.data.identity | data | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.data.log_return | data | accepted | reference_semantics | uses previous timestamp only | semantic_float64 | reject_or_declared_by_token | non-positive current or previous value emits diagnostic error |
| core.data.pct_change | data | accepted | reference_semantics | uses previous timestamp only | semantic_float64 | reject_or_declared_by_token | previous value zero emits diagnostic error |
| core.data.shift | data | accepted | reference_semantics | positive periods lag; negative periods require unsafe-future diagnostics | semantic_float64 | reject_or_declared_by_token | negative periods emit unsafe-future diagnostic unless explicitly allowed |
| core.decision.lift_bool | decision | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.gate.circuit_breaker | gate | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | breach threshold emits DecisionKind block; errors remain diagnostics |
| core.gate.cooldown | gate | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | gate block emits DecisionKind block; errors remain diagnostics |
| core.gate.market_freeze | gate | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | market freeze emits DecisionKind block; errors remain diagnostics |
| core.gate.observe_period | gate | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | observe warmup emits DecisionKind block; errors remain diagnostics |
| core.gate.slot_budget | gate | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | slot budget breach emits DecisionKind block; errors remain diagnostics |
| core.indicator.bollinger | indicator | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.indicator.channel_breakout | indicator | accepted | reference_semantics | uses previous trailing window only to avoid current-bar lookahead | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.indicator.ema | indicator | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.indicator.rsi | indicator | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.indicator.sma | indicator | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.logic.and | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.logic.not | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.logic.or | bool | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.math.abs | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.add | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.ceil | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.clip | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | lower greater than upper emits diagnostic error |
| core.math.div | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | division_by_zero emits diagnostic error |
| core.math.exp | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.fill_nan | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | NaN values are replaced by explicit replacement parameter | diagnostic_error |
| core.math.floor | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.isfinite | math | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | declared finite predicate handling | diagnostic_error |
| core.math.isnan | math | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | declared NaN predicate handling | diagnostic_error |
| core.math.log | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | non-positive input emits diagnostic error |
| core.math.max | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | empty input emits diagnostic error unless allow_empty=true |
| core.math.min | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | empty input emits diagnostic error unless allow_empty=true |
| core.math.mul | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.neg | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.pow | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.round | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.sign | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.sqrt | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | negative input emits diagnostic error |
| core.math.sub | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.math.where | math | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.norm.range_position | signal | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.optimizer.mean_variance | optimizer | experimental | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.risk.position_cap | risk | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | position cap breach emits DecisionKind block; errors remain diagnostics |
| core.risk.turnover_cap | risk | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | missing previous weight emits diagnostic error |
| core.risk.volatility_target | risk | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | missing or nonpositive volatility emits diagnostic error |
| core.score.calibrate | continuous_score | experimental | validation_only | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.score.zscore | continuous_score | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.signal.cross_above | signal | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.signal.cross_below | signal | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.signal.crosses | signal | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.signal.threshold_above | signal | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.signal.threshold_below | signal | accepted | reference_semantics | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.smooth.linear_recursive | signal | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.time.session_filter | time | accepted | reference_semantics | declared_by_ports | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.window.count | window | accepted | reference_semantics | trailing window; min_history_bars derives from window parameter | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.window.max | window | accepted | reference_semantics | trailing window; min_history_bars derives from window parameter | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.window.mean | window | accepted | reference_semantics | trailing window; min_history_bars derives from window parameter | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.window.min | window | accepted | reference_semantics | trailing window; min_history_bars derives from window parameter | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.window.std | window | accepted | reference_semantics | trailing window; min_history_bars derives from window parameter | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.window.sum | window | accepted | reference_semantics | trailing window; min_history_bars derives from window parameter | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.window.zscore | window | accepted | reference_semantics | trailing window; zero variance outputs 0 | semantic_float64 | reject_or_declared_by_token | diagnostic_error |
| core.decision.any_accept | decision | accepted | reference_semantics | inherits_input_decision_events | score annotation ignored unless score_policy is declared | unknown DecisionKind handled by policy | validation_result_diagnostics |
| core.decision.majority | decision | accepted | reference_semantics | inherits_input_decision_events | score annotation ignored unless score_policy is declared | unknown DecisionKind handled by policy | validation_result_diagnostics |
| core.decision.permissive_and | decision | accepted | reference_semantics | inherits_input_decision_events | score annotation ignored unless score_policy is declared | unknown DecisionKind handled by policy | validation_result_diagnostics |
| core.decision.quorum | decision | accepted | reference_semantics | inherits_input_decision_events | score annotation ignored unless score_policy is declared | unknown DecisionKind handled by policy | validation_result_diagnostics |
| core.decision.strict_and | decision | accepted | reference_semantics | inherits_input_decision_events | score annotation ignored unless score_policy is declared | unknown DecisionKind handled by policy | validation_result_diagnostics |
| core.decision.unknown_propagating_and | decision | accepted | reference_semantics | inherits_input_decision_events | score annotation ignored unless score_policy is declared | unknown DecisionKind handled by policy | validation_result_diagnostics |
| core.decision.weighted_vote | decision | accepted | reference_semantics | inherits_input_decision_events | score annotation ignored unless score_policy is declared | unknown DecisionKind handled by policy | validation_result_diagnostics |
| core.panel.bottom_k | panel | accepted | reference_semantics | panel operators join input port temporal metadata | declared_by_numeric_policy | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.demean | panel | accepted | reference_semantics | panel operators join input port temporal metadata | semantic_float64 | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.group_demean | panel | accepted | reference_semantics | panel operators join input port temporal metadata | semantic_float64 | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.mask | panel | accepted | reference_semantics | panel operators join input port temporal metadata | declared_by_numeric_policy | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.rank | panel | accepted | reference_semantics | panel operators join input port temporal metadata | semantic_float64 | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.residualize | panel | accepted | reference_semantics | panel operators join input port temporal metadata | semantic_float64 | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.top_k | panel | accepted | reference_semantics | panel operators join input port temporal metadata | declared_by_numeric_policy | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.winsorize | panel | accepted | reference_semantics | panel operators join input port temporal metadata | semantic_float64 | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.panel.zscore | panel | accepted | reference_semantics | panel operators join input port temporal metadata | semantic_float64 | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.selection.to_weights | weight | accepted | reference_semantics | panel operators join input port temporal metadata | declared_by_numeric_policy | UniverseMask=false is out-of-universe; active missing values follow missing_policy | validation_result_diagnostics |
| core.weight.cap_per_symbol | weight | accepted | reference_semantics | weight operators join input port temporal metadata | decimal canonical weight arithmetic with semantic reference rules | UniverseMask=false is out-of-universe; active missing weights follow missing_policy | validation_result_diagnostics |
| core.weight.market_neutral | weight | accepted | reference_semantics | weight operators join input port temporal metadata | decimal canonical weight arithmetic with semantic reference rules | UniverseMask=false is out-of-universe; active missing weights follow missing_policy | validation_result_diagnostics |
| core.weight.normalize_gross | weight | accepted | reference_semantics | weight operators join input port temporal metadata | decimal canonical weight arithmetic with semantic reference rules | UniverseMask=false is out-of-universe; active missing weights follow missing_policy | validation_result_diagnostics |
| core.state.accumulate | state | accepted | reference_semantics | state evolves in input order; reset before current event | declared_by_numeric_policy | state policy controls missing input behavior | validation_result_diagnostics |
| core.state.delay | state | accepted | reference_semantics | state evolves in input order; reset before current event | declared_by_numeric_policy | state policy controls missing input behavior | validation_result_diagnostics |
| core.state.edge_detect | state | accepted | reference_semantics | state evolves in input order; reset before current event | declared_by_numeric_policy | state policy controls missing input behavior | validation_result_diagnostics |
| core.state.fsm | state | accepted | reference_semantics | state evolves in input order; reset before current event | declared_by_numeric_policy | state policy controls missing input behavior | validation_result_diagnostics |

## Pass With Warning

No accepted token requires repair before Stage 3B acceptance. The warnings below are accepted metadata-only plan shells, not executable token gaps.

| TokenRef | Family | Maturity | Scope | Temporal | Numeric | Missing Data | Finding |
|---|---|---|---|---|---|---|---|
| core.plan.noop | execution | accepted | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error  accepted metadata-only shell |
| core.plan.order_intent | execution | accepted | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error  accepted metadata-only shell |

## Reserved By Design

| TokenRef | Family | Maturity | Scope | Temporal | Numeric | Missing Data | Failure Mode |
|---|---|---|---|---|---|---|---|
| core.distribution.normal_fit | distribution | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.distribution.quantile | distribution | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.distribution.tail_probability | distribution | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.event.filter | event | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.event.join_asof | event | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.event.window_count | event | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.execution.cancel_order | execution | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.execution.fill_report | execution | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |
| core.execution.submit_order | execution | reserved_design | validation_only | declared_by_ports | declared_by_numeric_policy | reject_or_declared_by_token | diagnostic_error |

## Decision

The Stage 3A token contracts are accepted. Optimizer and execution-boundary capabilities remain metadata-only where deterministic runtime contracts do not exist.
