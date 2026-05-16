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

## Hash Impact

| Object | Stage 3A impact |
| --- | --- |
| TokenSpec hash | Changes when surface or contract metadata changes. |
| TokenPack hash | Changes when contained TokenSpec hashes change. |
| Strategy graph hash | Unchanged unless graph topology or token refs change. |
| Strategy param hash | Unchanged unless parameters change. |
| Strategy instance hash | Derived from graph and param hashes in the current implementation. |

Reference demo hash sentinels live under `tests/reference/strategies/`.
