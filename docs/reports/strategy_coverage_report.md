# Strategy Coverage Report

Generated from `docs/reports/strategy_coverage_matrix.yaml`.

This report measures the QST strategy record layer only. It does not claim broker,
exchange, live execution, HFT runtime, full backtest engine, production execution,
profitability, or portfolio optimizer coverage.

## Summary

- Pattern count: `101`
- Frontier pattern count: `100`
- Dogfood pattern count: `1`
- Total frontier weight: `517.0`
- Check result: `pass`

## Benchmark Groups

| Group | Count | Weight | Supported | Partial | Custom | Reserved | Non-goal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dogfood | 1 | 5.0 | 0 | 1 | 0 | 0 | 0 |
| external_benchmark | 20 | 102.0 | 9 | 2 | 3 | 4 | 2 |
| internal_matrix | 80 | 415.0 | 46 | 12 | 12 | 7 | 3 |

## Classification Summary

| Classification | Count | Weight |
| --- | ---: | ---: |
| custom_token_required | 15 | 79.0 |
| non_goal | 5 | 19.0 |
| partially_supported | 15 | 78.0 |
| reserved | 11 | 42.0 |
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
| kernel_gap_count | 23 |
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

- Status: `dogfood_mvp`
- Classifications: `partially_supported`

| Row | Status | Classification | Candidate GKR | Evidence report | Limitations |
| --- | --- | --- | --- | --- | --- |
| dog_001_original_multi_asset_mean_reversion_grid | dogfood_mvp | partially_supported | tests/coverage_cases/dogfood/original_multi_asset_mean_reversion_grid.partial.gkr.yaml | docs/reports/original_failure_strategy_dogfood.md | Partial record shell only; no staged grid add execution.; No VWAP add optimizer, BTC-led regime model, live order lifecycle, broker/exchange execution, or account feedback runtime. |

Dogfood rows remain excluded from headline frontier percentages until the
frontier publication target dogfood set is complete or explicitly deferred.

## Validation

- Validator result: `pass`
- Validator issue count: `0`
- Report check result: `pass`
- Report check issue count: `0`
