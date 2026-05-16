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

## Hash Impact

| Object | Stage 3A impact |
| --- | --- |
| TokenSpec hash | Changes when surface or contract metadata changes. |
| TokenPack hash | Changes when contained TokenSpec hashes change. |
| Strategy graph hash | Unchanged unless graph topology or token refs change. |
| Strategy param hash | Unchanged unless parameters change. |
| Strategy instance hash | Derived from graph and param hashes in the current implementation. |

Reference demo hash sentinels live under `tests/reference/strategies/`.
