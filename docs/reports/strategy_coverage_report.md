# Strategy Coverage Report

Generated from `docs/reports/strategy_coverage_matrix.yaml`.

This report measures the QST strategy record layer only. It does not claim broker,
exchange, live execution, HFT runtime, full backtest engine, production execution,
profitability, or portfolio optimizer coverage.

## Summary

- Pattern count: `115`
- Frontier pattern count: `110`
- Dogfood pattern count: `5`
- Total frontier weight: `567.0`
- Check result: `pass`

## Benchmark Groups

| Group | Count | Weight | Supported | Partial | Custom | Reserved | Non-goal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dogfood | 5 | 25.0 | 0 | 3 | 1 | 1 | 0 |
| external_benchmark | 20 | 102.0 | 9 | 2 | 3 | 4 | 2 |
| internal_matrix | 90 | 465.0 | 62 | 11 | 7 | 7 | 3 |

## Classification Summary

| Classification | Count | Weight |
| --- | ---: | ---: |
| custom_token_required | 11 | 58.0 |
| non_goal | 5 | 19.0 |
| partially_supported | 16 | 82.0 |
| reserved | 12 | 47.0 |
| supported | 71 | 386.0 |

## Metrics

| Metric | Value |
| --- | ---: |
| direct_builtin_coverage | 0.2381 |
| routable_record_coverage_raw | 0.8924 |
| routable_record_coverage_discounted | 0.8457 |
| custom_token_route_share | 0.1047 |
| false_supported_rate_mechanical | 0.0000 |
| false_supported_rate_semantic | 0.0000 |
| false_supported_rate_boundary | 0.0000 |
| boundary_false_supported_count | 0 |
| kernel_gap_count | 18 |
| token_bloat_index | 0.1455 |

## Next Best Expansions

| Family or kernel | Type | Weighted gain | Complexity cost | Coverage efficiency |
| --- | --- | ---: | ---: | ---: |
| indicator.kdj | token | 12.0 | 1 | 12.0 |
| risk.stop_loss_record | token | 11.0 | 1 | 11.0 |
| risk.trailing_stop_record | token | 11.0 | 1 | 11.0 |
| port_temporal_type_gap | kernel | 27.0 | 3 | 9.0 |
| fsm_state_gap | kernel | 26.0 | 3 | 8.6667 |
| numeric_determinism_gap | kernel | 20.0 | 3 | 6.6667 |
| built-in Kalman signal | token | 6.0 | 1 | 6.0 |
| pair_spread_model | token | 6.0 | 1 | 6.0 |
| bollinger_bandwidth recipe | token | 5.0 | 1 | 5.0 |
| gate.drawdown recipe | token | 5.0 | 1 | 5.0 |

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
