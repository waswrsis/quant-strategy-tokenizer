# Strategy Coverage Report

Generated from `docs/reports/strategy_coverage_matrix.yaml`.

This report measures the QST strategy record layer only. It does not claim broker,
exchange, live execution, HFT runtime, full backtest engine, production execution,
profitability, or portfolio optimizer coverage.

## Summary

- Pattern count: `105`
- Frontier pattern count: `100`
- Dogfood pattern count: `5`
- Total frontier weight: `517.0`
- Check result: `pass`

## Benchmark Groups

| Group | Count | Weight | Supported | Partial | Custom | Reserved | Non-goal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dogfood | 5 | 25.0 | 0 | 3 | 1 | 1 | 0 |
| external_benchmark | 20 | 102.0 | 9 | 2 | 3 | 4 | 2 |
| internal_matrix | 80 | 415.0 | 46 | 12 | 12 | 7 | 3 |

## Classification Summary

| Classification | Count | Weight |
| --- | ---: | ---: |
| custom_token_required | 16 | 84.0 |
| non_goal | 5 | 19.0 |
| partially_supported | 17 | 88.0 |
| reserved | 12 | 47.0 |
| supported | 55 | 304.0 |

## Metrics

| Metric | Value |
| --- | ---: |
| direct_builtin_coverage | 0.1412 |
| routable_record_coverage_raw | 0.8820 |
| routable_record_coverage_discounted | 0.8056 |
| custom_token_route_share | 0.1732 |
| false_supported_rate_mechanical | 0.0000 |
| false_supported_rate_semantic | 0.0000 |
| false_supported_rate_boundary | 0.0000 |
| boundary_false_supported_count | 0 |
| kernel_gap_count | 20 |
| token_bloat_index | 0.2200 |

## Next Best Expansions

| Family or kernel | Type | Weighted gain | Complexity cost | Coverage efficiency |
| --- | --- | ---: | ---: | ---: |
| indicator.kdj | token | 12.0 | 1 | 12.0 |
| risk.stop_loss_record | token | 11.0 | 1 | 11.0 |
| risk.trailing_stop_record | token | 11.0 | 1 | 11.0 |
| port_temporal_type_gap | kernel | 27.0 | 3 | 9.0 |
| fsm_state_gap | kernel | 26.0 | 3 | 8.6667 |
| numeric_determinism_gap | kernel | 25.0 | 3 | 8.3333 |
| built-in Kalman signal | token | 6.0 | 1 | 6.0 |
| factor.sector_neutral_rank recipe | token | 6.0 | 1 | 6.0 |
| indicator.macd | token | 6.0 | 1 | 6.0 |
| pair_spread_model | token | 6.0 | 1 | 6.0 |

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
