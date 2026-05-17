# Strategy Coverage Report

Generated from `docs/reports/strategy_coverage_matrix.yaml`.

This report measures the QST strategy record layer only. It does not claim broker,
exchange, live execution, HFT runtime, full backtest engine, production execution,
profitability, or portfolio optimizer coverage.

## Summary

- Pattern count: `120`
- Frontier pattern count: `115`
- Dogfood pattern count: `5`
- Total frontier weight: `592.0`
- Check result: `pass`

## Benchmark Groups

| Group | Count | Weight | Supported | Partial | Custom | Reserved | Non-goal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dogfood | 5 | 25.0 | 0 | 3 | 1 | 1 | 0 |
| external_benchmark | 20 | 102.0 | 11 | 0 | 3 | 4 | 2 |
| internal_matrix | 95 | 490.0 | 77 | 2 | 6 | 7 | 3 |

## Classification Summary

| Classification | Count | Weight |
| --- | ---: | ---: |
| custom_token_required | 10 | 54.0 |
| non_goal | 5 | 19.0 |
| partially_supported | 5 | 25.0 |
| reserved | 12 | 47.0 |
| supported | 88 | 472.0 |

## Metrics

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

PR10 records governance evidence for active custom-token routes. These routes
remain record-layer classification evidence only; verification may inspect
metadata and integrity, but it does not approve, grant, or execute custom code.

- Route share: `0.0923`
- Route cap: `0.4000`
- Discount: `0.5000` (`provisional`)
- Active custom routes: `10`
- Missing governance rows: `0`
- Stale route findings: `0`

| Row | Reason | Missing tokens | Future built-in candidate | Remain custom route |
| --- | --- | --- | --- | --- |
| dog_004_custom_ml_score_signal | The score model is external code and cannot be represented as an accepted built-in token. | built-in ML score model | false | true |
| ext_005_pairs_trade | Spread construction/cointegration model is strategy-specific. | pair_spread_model | true | true |
| ext_013_ml_classifier_signal | Model implementation is external code. | none | false | true |
| ext_014_sentiment_signal | Sentiment extraction is external model/data logic. | none | false | true |
| int_012_custom_kalman | Kalman signal is external/custom logic. | built-in Kalman signal | true | true |
| int_013_kdj_cross_basic | KDJ signal has no accepted built-in token. | indicator.kdj | true | true |
| int_014_kdj_with_ema_filter | KDJ component is custom; EMA filter is built-in. | indicator.kdj | true | true |
| int_052_score_calibrate | score.calibrate is experimental metadata-only. | accepted score.calibrate semantics | true | true |
| int_053_custom_ml_score | Model implementation is external code. | none | false | true |
| int_054_custom_panel_factor | Factor logic is external/proprietary. | none | false | true |

| Retired stale route | Replacement evidence |
| --- | --- |
| int_040_net_normalize | tests/coverage_cases/panel_factor_weight/group_neutral_net_normalize_weights.partial.gkr.yaml, tests/coverage_cases/panel_factor_weight/group_neutral_net_normalize_weights.hashes.json |

## Next Best Expansions

| Family or kernel | Type | Weighted gain | Complexity cost | Coverage efficiency |
| --- | --- | ---: | ---: | ---: |
| indicator.kdj | token | 12.0 | 1 | 12.0 |
| port_temporal_type_gap | kernel | 27.0 | 3 | 9.0 |
| numeric_determinism_gap | kernel | 20.0 | 3 | 6.6667 |
| built-in Kalman signal | token | 6.0 | 1 | 6.0 |
| pair_spread_model | token | 6.0 | 1 | 6.0 |
| bollinger_bandwidth recipe | token | 5.0 | 1 | 5.0 |
| risk.rebalance_calendar | token | 5.0 | 1 | 5.0 |
| accepted score.calibrate semantics | token | 4.0 | 1 | 4.0 |

## Core rule token batch

PR6 adds accepted record/reference token coverage for common indicator, signal,
and decision-rule patterns. These rows remain record-layer evidence and do not
claim broad runtime execution, broker/exchange behavior, or profitability.

| Row | Classification | Mechanical status | Example | Required tokens |
| --- | --- | --- | --- | --- |
| int_020_macd_trend | supported | pass | tests/coverage_cases/core_rule/macd_trend.partial.gkr.yaml | indicator.macd, signal.greater_than, decision.long_flat |
| int_021_atr_filter | supported | pass | tests/coverage_cases/core_rule/atr_filter.partial.gkr.yaml | indicator.atr, signal.less_than, decision.long_flat |
| int_022_linear_regression_slope | supported | pass | tests/coverage_cases/core_rule/linear_regression_slope.partial.gkr.yaml | indicator.linear_regression_slope, decision.signal_to_decision |
| int_081_signal_composition | supported | pending | pending | signal.and, signal.or, signal.not, signal.between, signal.outside_band |
| int_082_decision_long_short_rule | supported | pass | tests/coverage_cases/core_rule/long_short_decision.partial.gkr.yaml | indicator.donchian_channel, signal.breakout_up, signal.breakout_down, decision.long_short |
| int_083_entry_exit_gate_record | supported | pending | pending | decision.entry_exit_to_position, decision.gate_decision |
| int_084_beta_residual_timeseries | supported | pass | tests/coverage_cases/core_rule/beta_residual_timeseries.partial.gkr.yaml | indicator.beta, indicator.residual, signal.zscore_revert, decision.long_flat |
| int_085_donchian_volatility_rule | supported | pending | pending | indicator.donchian_channel, indicator.volatility, signal.breakout_up, signal.breakout_down |

## Panel / Factor / Weight Batch

PR8 adds accepted record/reference token coverage for panel aliases,
factor records, and deterministic weight transforms. These rows remain
record-layer evidence and do not claim optimizer, rebalance, broker,
exchange, live execution, or profitability coverage.

| Row | Classification | Mechanical status | Example | Required tokens |
| --- | --- | --- | --- | --- |
| int_041_inverse_vol_weight | supported | pass | tests/coverage_cases/panel_factor_weight/inverse_vol_weight.partial.gkr.yaml | weight.inverse_vol_weight |
| int_049_sector_neutral_rank | supported | pass | tests/coverage_cases/panel_factor_weight/sector_neutral_rank.partial.gkr.yaml | factor.sector_neutral_rank, selection.top_k |
| int_050_beta_neutral_signal | supported | pass | tests/coverage_cases/panel_factor_weight/beta_neutral_signal.partial.gkr.yaml | factor.beta_neutral_signal, decision.signal_to_decision |
| int_086_panel_alias_records | supported | pass | tests/coverage_cases/panel_factor_weight/sector_neutral_rank.partial.gkr.yaml | panel.cross_sectional_rank, panel.zscore_by_universe, panel.neutralize_group, selection.top_k, selection.bottom_k |
| int_087_equal_rank_weight_records | supported | pass | tests/coverage_cases/panel_factor_weight/equal_rank_market_neutral_weights.partial.gkr.yaml | weight.equal_weight, weight.rank_weight, weight.market_neutral_weight |
| int_088_group_neutral_weight_record | supported | pass | tests/coverage_cases/panel_factor_weight/group_neutral_net_normalize_weights.partial.gkr.yaml | weight.group_neutral_weight, weight.max_weight_clip, weight.normalize_net |
| int_089_inverse_volatility_weight_record | supported | pass | tests/coverage_cases/panel_factor_weight/inverse_vol_weight.partial.gkr.yaml | weight.inverse_vol_weight |
| int_090_weight_vol_target_wrapper | supported | pending | pending | weight.vol_target_weight, risk.volatility_target |

## State / Gate / Risk Batch

PR9 adds accepted record/reference token coverage for common state, gate,
stop/take-profit, drawdown, exposure, turnover, and rebalance-band records.
These rows remain record-layer evidence and do not claim broker/exchange
execution, live stop orders, backtests, account runtime, or Calendar/EventStream
support.

| Row | Classification | Mechanical status | Example | Required tokens |
| --- | --- | --- | --- | --- |
| int_027_min_hold_gate | supported | pass | tests/coverage_cases/state_gate_risk/min_max_hold_gate.partial.gkr.yaml | gate.min_hold |
| int_028_max_hold_gate | supported | pass | tests/coverage_cases/state_gate_risk/min_max_hold_gate.partial.gkr.yaml | gate.max_hold |
| int_029_trailing_stop_record | supported | pass | tests/coverage_cases/state_gate_risk/trailing_stop_record.partial.gkr.yaml | risk.trailing_stop_record |
| int_030_stop_loss_record | supported | pass | tests/coverage_cases/state_gate_risk/stop_take_profit_records.partial.gkr.yaml | risk.stop_loss_record |
| int_031_take_profit_record | supported | pass | tests/coverage_cases/state_gate_risk/stop_take_profit_records.partial.gkr.yaml | risk.take_profit_record |
| int_032_rebalance_band | supported | pass | tests/coverage_cases/state_gate_risk/rebalance_time_window_records.partial.gkr.yaml | gate.rebalance, risk.turnover_limit_record |
| int_035_exposure_cap | supported | pass | tests/coverage_cases/state_gate_risk/exposure_turnover_limit_records.partial.gkr.yaml | risk.exposure_cap_record |
| int_055_volatility_regime_gate | supported | pass | tests/coverage_cases/state_gate_risk/drawdown_volatility_regime.partial.gkr.yaml | gate.volatility_regime |
| int_056_drawdown_gate | supported | pass | tests/coverage_cases/state_gate_risk/drawdown_volatility_regime.partial.gkr.yaml | gate.drawdown, risk.max_drawdown_record |
| int_091_state_hold_gate_records | supported | pass | tests/coverage_cases/state_gate_risk/min_max_hold_gate.partial.gkr.yaml | gate.min_hold, gate.max_hold |
| int_092_stop_take_profit_risk_records | supported | pass | tests/coverage_cases/state_gate_risk/stop_take_profit_records.partial.gkr.yaml | risk.stop_loss_record, risk.take_profit_record |
| int_093_trailing_drawdown_risk_records | supported | pass | tests/coverage_cases/state_gate_risk/trailing_stop_record.partial.gkr.yaml | risk.trailing_stop_record, risk.max_drawdown_record, gate.drawdown |
| int_094_volatility_regime_time_window_records | supported | pass | tests/coverage_cases/state_gate_risk/drawdown_volatility_regime.partial.gkr.yaml | gate.volatility_regime, gate.time_window |
| int_095_rebalance_exposure_turnover_records | supported | pass | tests/coverage_cases/state_gate_risk/exposure_turnover_limit_records.partial.gkr.yaml | gate.rebalance, risk.exposure_cap_record, risk.turnover_limit_record, risk.volatility_target_record |

## Dogfood

- Status: `dogfood_mvp, dogfood_target`
- Classifications: `custom_token_required, partially_supported, reserved`
- MVP target: `5 / 1` (`pass`)
- Publication target: `5 / 5` (`pass`)

| Row | Status | Classification | Candidate GKR | Evidence report | Limitations |
| --- | --- | --- | --- | --- | --- |
| dog_001_original_multi_asset_mean_reversion_grid | dogfood_mvp | partially_supported | tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml | docs/reports/original_failure_strategy_dogfood.md | Partial record shell only; no staged grid add execution.; No VWAP add optimizer, BTC-led regime model, live order lifecycle, broker/exchange execution, or account feedback runtime. |
| dog_002_single_asset_trend_following_fsm | dogfood_target | partially_supported | tests/coverage_cases/dogfood/single_asset_trend_following_fsm.partial.gkr.yaml | docs/reports/dogfood_target_set.md | Partial record shell only; no full FSM transition lifecycle.; No broker-side stop order, position lifecycle, or fill feedback runtime. |
| dog_003_cross_sectional_factor_panel | dogfood_target | partially_supported | tests/coverage_cases/dogfood/cross_sectional_factor_panel.partial.gkr.yaml | docs/reports/dogfood_target_set.md | Partial record shell only; no factor construction governance.; No sector metadata, optimizer, rebalance scheduler, broker, or exchange execution. |
| dog_004_custom_ml_score_signal | dogfood_target | custom_token_required | not recorded | docs/reports/dogfood_target_set.md | No custom Python import, approval, grant, or execution is part of this dogfood record. |
| dog_005_reserved_event_stream_orderbook | dogfood_target | reserved | not recorded | docs/reports/dogfood_target_set.md | No candidate GKR is attempted; do not fake order-book events as ordinary time series. |

Dogfood rows remain excluded from headline frontier percentages. The publication
target records breadth evidence for the dogfood set, not runtime execution or
profitability.

## Validation

- Validator result: `pass`
- Validator issue count: `0`
- Report check result: `pass`
- Report check issue count: `0`
