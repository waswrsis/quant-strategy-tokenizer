# QST Taxonomy

This taxonomy records the P0 frozen vocabulary and the P1-core additions. P1-core may add vocabulary, but it must not rename or change the P0 `(id, version, behavior_version)` triples.

## Computation Tokens

| Token | Version | Behavior Version | Category | Outputs | Status |
|---|---:|---:|---|---|---|
| `data.column` | 1 | 1 | data | `value: TimeSeries[float]` | P0 frozen |
| `data.shift` | 1 | 1 | data | `value: TimeSeries[float]` | P0 frozen |
| `window.max` | 1 | 1 | window | `value: TimeSeries[float]` | P0 frozen |
| `window.min` | 1 | 1 | window | `value: TimeSeries[float]` | P0 frozen |
| `smooth.linear_recursive` | 1 | 1 | smooth | `value: TimeSeries[float]` | P0 frozen |
| `math.add` | 1 | 1 | math | `value: TimeSeries[float]` | P0 frozen |
| `math.sub` | 1 | 1 | math | `value: TimeSeries[float]` | P0 frozen |
| `math.mul` | 1 | 1 | math | `value: TimeSeries[float]` | P0 frozen |
| `math.div` | 1 | 1 | math | `value: TimeSeries[float]` | P0 frozen |
| `math.linear_combination` | 1 | 1 | math | `value: TimeSeries[float]` | P0 frozen |
| `compare.gt` | 1 | 1 | compare | `value: TimeSeries[bool]` | P0 frozen |
| `compare.le` | 1 | 1 | compare | `value: TimeSeries[bool]` | P0 frozen |
| `compare.ge` | 1 | 1 | compare | `value: TimeSeries[bool]` | P1-core |
| `compare.lt` | 1 | 1 | compare | `value: TimeSeries[bool]` | P1-core |
| `logic.and` | 1 | 1 | logic | `value: TimeSeries[bool]` | P0 frozen |
| `norm.range_position` | 1 | 1 | norm | `value: TimeSeries[float]` | P0 frozen |

## Infrastructure Tokens

| Token | Version | Behavior Version | Category | Outputs | Status |
|---|---:|---:|---|---|---|
| `decision.lift_bool` | 1 | 1 | decision | `decision: Decision` | P0 frozen |
| `decision.reduce` | 1 | 1 | decision | `decision: Decision` | P0 frozen |
| `decision.reduce` | 2 | 1 | decision | `decision: Decision` | P1-core |
| `decision.map_status` | 1 | 1 | decision | `decision: Decision` | P1-core |
| `state.read_field` | 1 | 1 | state | `value: Scalar` | P1-core |
| `risk.position_cap` | 1 | 1 | risk | `decision: Decision` | P1-core |
| `risk.notional_cap` | 1 | 1 | risk | `decision: Decision` | P1-core |
| `plan.noop` | 1 | 1 | plan | `plan: Plan` | P0 frozen |
| `plan.order_intent` | 1 | 1 | plan | `plan: Plan` | P1-core |

## Recipes

| Recipe | Version | Outputs | Status |
|---|---:|---|---|
| `indicator.ewm` | 1 | `value` | P0 frozen |
| `indicator.rma` | 1 | `value` | P0 frozen |
| `indicator.kdj` | 1 | `k`, `d`, `j` | P0 frozen |
| `event.cross_above` | 1 | `cross` | P0 frozen |
| `event.threshold_above` | 1 | `cross` | P1-core |
| `event.threshold_below` | 1 | `cross` | P1-core |
| `gate.elapsed_threshold` | 1 | `gate` | P1-core |
| `gate.cooldown` | 1 | `gate` | P1-core |

## Profiles

| Profile | Meaning |
|---|---|
| `research` | Default profile. No pretrade risk-path requirement. |
| `paper` | Simulation profile. Same content hash semantics as research. |
| `pretrade` | Requires `plan.order_intent` to have a `risk.*` ancestor. |
| `production_guarded` | Same P1-core risk-path gate as pretrade. |
