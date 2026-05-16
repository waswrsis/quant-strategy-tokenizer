# Token Coverage

Stage 3A adds conformance gates for the public built-in vocabulary:

- every built-in TokenSpec has `surface` metadata;
- accepted tokens have temporal, numeric, missing-data, and failure-mode contracts;
- experimental, deprecated, and reserved-design tokens are gated by profile;
- built-in TokenPacks are returned by `builtin_token_packs()` in deterministic order;
- all public demos have validation artifacts and graph/param/instance hash sentinels.

Stage 3A.1 adds concrete primitive coverage for `math.*`, `bool.*`, and
`cmp.*` token contracts. The helper implementations are deterministic reference
semantics for tests and demos; they are not a broad GKR execution runtime.

The primitive coverage fixes:

- numeric domain errors for divide-by-zero, negative square root, non-positive
  logarithm, non-finite input, and bool-as-float input;
- boolean truth tables and explicit empty-input policies for boolean folds;
- comparison truth tables with inclusive range boundaries by default.

Stage 3A.2 adds accepted data/time/align/window/signal/indicator coverage.
Series reference helpers use `Sequence[tuple[str, value]]` test material,
canonical timestamp ordering, and duplicate-timestamp diagnostics. Numeric
series reject bool, NaN, and Infinity. The helpers are intentionally separate
from strategy validation and do not create a broad runtime.

The series coverage fixes:

- unsafe future behavior for negative `data.shift` periods;
- return-transform domain errors for zero percentage-change denominators and
  non-positive log-return inputs;
- trailing-window behavior, `min_periods`, population standard deviation, and
  zero-variance z-score output;
- cross/threshold signal truth tables and current-bar-safe channel breakout.

Stage 3A.3 adds decision/gate/state conformance coverage:

- `decision.lift_bool` and Decision Algebra facade delegation;
- monoid/fold/aggregator classification for decision tokens;
- state helper facade coverage that preserves existing traces and diagnostics;
- gate reference fixtures for cooldown, market freeze, circuit breaker, observe
  period, and slot budget behavior.

Gate helpers output `DecisionV2` values only. Diagnostics remain diagnostics and
do not become a DecisionKind.

Stage 3A.4 adds panel/weight/risk/optimizer conformance coverage:

- panel and weight token surface contracts preserve accepted WP8 semantics;
- panel float operators are explicitly semantic float64 and make no bit-exact
  claim;
- weight operators use canonical decimal reference arithmetic;
- risk helpers cover position-cap blocking, volatility-target scaling, and
  turnover-cap clipping without optimization, redistribution, order planning, or
  broker execution;
- optimizer tokens are experimental, solver-backed, and metadata-only until a
  deterministic solver contract is accepted.

## Hash Impact

| Object | Stage 3A impact |
| --- | --- |
| TokenSpec hash | Changes when surface or contract metadata changes. |
| TokenPack hash | Changes when contained TokenSpec hashes change. |
| Strategy graph hash | Unchanged unless graph topology or token refs change. |
| Strategy param hash | Unchanged unless parameters change. |
| Strategy instance hash | Derived from graph and param hashes in the current implementation. |

Reference demo hash sentinels live under `tests/reference/strategies/`.
