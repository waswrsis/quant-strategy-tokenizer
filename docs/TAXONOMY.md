# QST Taxonomy

This taxonomy records the frozen P0 vocabulary and the accepted P1-core additions. It is also the P1-extended-a metadata checklist for purity and temporal safety.

## P0 Frozen Tokens

| id | version | behavior_version | layer | category | lifecycle | purity | uses_future_data | window_mode | output_available_at | max_lookback | profile_allowed | status |
|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| `data.column` | 1 | 1 | computation | data | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `data.shift` | 1 | 1 | computation | data | core_candidate | pure | false | trailing | same_bar_close | not_declared | all | P0 frozen |
| `window.max` | 1 | 1 | computation | window | core_candidate | pure | false | trailing | end_of_window | not_declared | all | P0 frozen |
| `window.min` | 1 | 1 | computation | window | core_candidate | pure | false | trailing | end_of_window | not_declared | all | P0 frozen |
| `smooth.linear_recursive` | 1 | 1 | computation | smooth | core_candidate | pure | false | trailing | same_bar_close | not_declared | all | P0 frozen |
| `math.add` | 1 | 1 | computation | math | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `math.sub` | 1 | 1 | computation | math | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `math.mul` | 1 | 1 | computation | math | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `math.div` | 1 | 1 | computation | math | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `math.linear_combination` | 1 | 1 | computation | math | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `compare.gt` | 1 | 1 | computation | compare | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `compare.le` | 1 | 1 | computation | compare | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `logic.and` | 1 | 1 | computation | logic | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `norm.range_position` | 1 | 1 | computation | norm | core_candidate | pure | false | none | same_bar_close | not_declared | all | P0 frozen |
| `decision.lift_bool` | 1 | 1 | infrastructure | decision | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P0 frozen |
| `decision.reduce` | 1 | 1 | infrastructure | decision | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P0 frozen |
| `plan.noop` | 1 | 1 | infrastructure | plan | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P0 frozen |

## P1-Core Tokens

| id | version | behavior_version | layer | category | lifecycle | purity | uses_future_data | window_mode | output_available_at | max_lookback | profile_allowed | status |
|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| `compare.ge` | 1 | 1 | computation | compare | core_candidate | pure | false | none | same_bar_close | not_declared | all | P1-core accepted |
| `compare.lt` | 1 | 1 | computation | compare | core_candidate | pure | false | none | same_bar_close | not_declared | all | P1-core accepted |
| `decision.map_status` | 1 | 1 | infrastructure | decision | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P1-core accepted |
| `decision.reduce` | 2 | 1 | infrastructure | decision | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P1-core accepted |
| `state.read_field` | 1 | 1 | infrastructure | state | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P1-core accepted |
| `risk.position_cap` | 1 | 1 | infrastructure | risk | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P1-core accepted |
| `risk.notional_cap` | 1 | 1 | infrastructure | risk | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P1-core accepted |
| `plan.order_intent` | 1 | 1 | infrastructure | plan | core_candidate | contextual_read | false | none | same_bar_close | not_declared | all | P1-core accepted |

## P0 Frozen Recipes

| id | version | purity | uses_future_data | window_mode | output_available_at | max_lookback | profile_allowed | status |
|---|---:|---|---|---|---|---|---|---|
| `indicator.ewm` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P0 frozen |
| `indicator.rma` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P0 frozen |
| `indicator.kdj` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P0 frozen |
| `event.cross_above` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P0 frozen |

## P1-Core Recipes

| id | version | purity | uses_future_data | window_mode | output_available_at | max_lookback | profile_allowed | status |
|---|---:|---|---|---|---|---|---|---|
| `event.threshold_above` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P1-core accepted |
| `event.threshold_below` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P1-core accepted |
| `gate.elapsed_threshold` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P1-core accepted |
| `gate.cooldown` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P1-core accepted |

## P2a-2 Algorithm Recipes

| id | version | purity | uses_future_data | window_mode | output_available_at | max_lookback | profile_allowed | status |
|---|---:|---|---|---|---|---|---|---|
| `signals.dual_ema_cross` | 1 | derived_from_graph | inherits_graph | inherits_graph | inherits_graph | not_declared | all | P2a-2 accepted |

## Profile Policy

| Profile | Max purity | Future data | Unsafe window modes |
|---|---|---|---|
| `research` | external_read | warning | warning |
| `paper` | external_read | warning | warning |
| `pretrade` | contextual_read | error | error |
| `production_guarded` | contextual_read | error | error |
