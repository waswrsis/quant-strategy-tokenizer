# Token Family Registry

Stage 3A organizes public tokens by family:

```text
math, bool, compare, data, time, align, window, signal, indicator,
decision, gate, state, panel, weight, risk, optimizer, execution,
event, distribution, continuous_score
```

Each built-in token must declare:

- `surface.family`
- `surface.category`
- `surface.layer`
- `surface.maturity`
- `surface.execution_support`
- `surface.contract`
- `surface.capabilities`
- `surface.agent_metadata`

## Maturity

| Maturity | Research | Paper | Pretrade | Production Guarded |
| --- | --- | --- | --- | --- |
| `accepted` | pass | pass | pass | pass |
| `frozen` | pass | pass | pass | pass |
| `experimental` | warning | warning | error | error |
| `deprecated` | warning | warning | warning | error |
| `reserved_design` | error | error | error | error |

## Execution Support

| Value | Meaning |
| --- | --- |
| `metadata_only` | Recognized and explainable; not executable. |
| `reference_helper` | Deterministic reference helper exists for tests or examples. |
| `runtime_executor` | Formal runtime executor exists. |
| `external_only` | Execution comes from an approved custom token or adapter boundary. |

`accepted` means the token governance and contract are accepted. It does not
imply broad strategy execution.

## Stage 3A.1 Primitive Families

Stage 3A.1 makes the canonical primitive surface explicit:

- `math.*`: arithmetic, reductions, transforms, predicates, conditionals, and
  missing-value transforms.
- `bool.*`: boolean logic and boolean reductions.
- `cmp.*`: numeric comparisons and range comparisons.

Existing `logic.*` and `compare.*` tokens remain accepted aliases for current
demo and reference material. New token authoring should prefer `bool.*` and
`cmp.*`. Cross-over semantics such as `crosses` belong to the `signal` family,
not the comparison family.

Primitive reference helpers are conformance helpers only. They do not create a
broad GKR runtime and are not invoked by validation.

## Stage 3A.2 Series Families

Stage 3A.2 completes the accepted series-token surface for:

- `data.*`: identity, shift, diff, percentage change, and log return.
- `time.*`: session filtering over timestamp time-of-day.
- `align.*`: inner join, left join, forward fill, and missing-row drop.
- `window.*`: trailing max/min/mean/std/sum/count/zscore.
- `signal.*`: cross, threshold, normalization, and simple recursive smoothing.
- `indicator.*`: SMA, EMA, RSI, Bollinger bands, and channel breakout.

All Stage 3A.2 helpers use deterministic reference semantics for conformance
only. Window tokens are trailing-window tokens; centered windows remain unsafe
temporal behavior. `data.shift` with negative periods is an unsafe-future
operation unless a reference test explicitly opts in.

## Stage 3A.3 Decision, Gate, and State Families

Stage 3A.3 completes the accepted decision/state control surface:

- `decision.*`: Decision Algebra monoids, fold policies, aggregators, and
  `decision.lift_bool`.
- `state.*`: delay, accumulate, edge detect, and closed-set FSM reference
  helpers.
- `gate.*`: cooldown, market freeze, circuit breaker, observe period, and slot
  budget gate semantics.

Decision monoids remain limited to `decision.unknown_propagating_and` and
`decision.any_accept`. `decision.strict_and` and `decision.permissive_and` are
fold policies, not monoids. `error` is never a DecisionKind; gate and state
failures use diagnostics. For `state.fsm`, `failure_policy="raise"` means emit
an error diagnostic in the reference helper, not raise a Python exception.

Gate tokens are stateful reference semantics. They are not order management,
portfolio risk enforcement, or broker/exchange execution.
