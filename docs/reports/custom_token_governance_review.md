# Custom Token Governance Review

Coverage Frontier PR10 reviews custom-token-required rows after PR9. The review
does not add built-in tokens and does not approve, grant, or execute custom
Python. It records route evidence, stale-route cleanup, and cap enforcement for
the coverage matrix.

## Policy

- Route manifest: `tests/coverage_cases/custom_token_governance/custom_token_routes.yaml`
- Route cap: `custom_token_route_max = 0.30` after the PR12 frontier publication gate
- Provisional discount: `0.5`
- Verification boundary: metadata and integrity only
- Approval, grant, and execution remain separate user-authorized steps

Custom-token routes count toward routable record coverage only. They never count
as direct built-in coverage and never imply runtime execution.

## Active Custom Routes

| Row | Route | Missing token/type | Future built-in candidate | Decision |
| --- | --- | --- | --- | --- |
| `int_012_custom_kalman` | Reference custom token | `built-in Kalman signal` | yes | Keep custom route; built-in Kalman is a future token candidate. |
| `int_013_kdj_cross_basic` | KDJ indicator candidate | `indicator.kdj` | yes | Keep custom route; PR10 does not implement KDJ. |
| `int_014_kdj_with_ema_filter` | KDJ plus built-in EMA | `indicator.kdj` | yes | Keep custom route for KDJ component only. |
| `int_052_score_calibrate` | Experimental score boundary | `accepted score.calibrate semantics` | yes | Keep custom route until accepted calibration semantics exist. |
| `int_053_custom_ml_score` | External model | none | no | Keep custom route; model implementation is external code. |
| `int_054_custom_panel_factor` | External panel factor | none | no | Keep custom route; factor implementation is external/proprietary. |
| `ext_005_pairs_trade` | Pair-spread model | `pair_spread_model` | yes | Keep custom route; pair spread/cointegration model is strategy-specific. |
| `ext_013_ml_classifier_signal` | External classifier | none | no | Keep custom route; classifier implementation is external model code. |
| `ext_014_sentiment_signal` | Sentiment model/data route | `Text/News input` | no | Keep custom route; text/news input remains outside current TypeSpec. |
| `dog_004_custom_ml_score_signal` | Dogfood external model | `built-in ML score model`, `Model artifact` | no | Keep custom route; dogfood record is governance evidence only. |

## Stale Route Cleanup

`int_040_net_normalize` was previously classified as `custom_token_required`
because `weight.normalize_net` was not accepted. PR8 added accepted
`weight.normalize_net` reference-helper semantics and candidate evidence:

- `tests/coverage_cases/panel_factor_weight/group_neutral_net_normalize_weights.partial.gkr.yaml`
- `tests/coverage_cases/panel_factor_weight/group_neutral_net_normalize_weights.hashes.json`

PR10 reclassifies `int_040_net_normalize` as `supported` record-layer evidence
and removes the stale custom-token route.

## Boundary Statement

This review is governance evidence only. It does not:

- import or execute custom Python
- create a local approval
- issue an execution grant
- weaken profile gates
- convert KDJ, Kalman, ML, sentiment, or pair-spread models into built-in tokens
- claim broker, exchange, live execution, backtesting, or profitability support

## Follow-Up Candidates

The report tool may continue to surface `indicator.kdj`, built-in Kalman signal,
and `pair_spread_model` as next-best token candidates. Those are future token
batches, not PR10 work.
