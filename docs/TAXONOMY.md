# QST P0 Taxonomy

## Computation Tokens

| Token | Category | Outputs |
|---|---|---|
| `data.column` | data | `value: TimeSeries[float]` |
| `data.shift` | data | `value: TimeSeries[float]` |
| `window.max` | window | `value: TimeSeries[float]` |
| `window.min` | window | `value: TimeSeries[float]` |
| `smooth.linear_recursive` | smooth | `value: TimeSeries[float]` |
| `math.add` | math | `value: TimeSeries[float]` |
| `math.sub` | math | `value: TimeSeries[float]` |
| `math.mul` | math | `value: TimeSeries[float]` |
| `math.div` | math | `value: TimeSeries[float]` |
| `math.linear_combination` | math | `value: TimeSeries[float]` |
| `compare.gt` | compare | `value: TimeSeries[bool]` |
| `compare.le` | compare | `value: TimeSeries[bool]` |
| `logic.and` | logic | `value: TimeSeries[bool]` |
| `norm.range_position` | norm | `value: TimeSeries[float]` |

## Infrastructure Tokens

| Token | Category | Outputs |
|---|---|---|
| `decision.lift_bool` | decision | `decision: Decision` |
| `decision.reduce` | decision | `decision: Decision` |
| `plan.noop` | plan | `plan: Plan` |

## Recipes

| Recipe | Outputs |
|---|---|
| `indicator.ewm` | `value` |
| `indicator.rma` | `value` |
| `indicator.kdj` | `k`, `d`, `j` |
| `event.cross_above` | `cross` |
