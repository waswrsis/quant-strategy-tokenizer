# QST P2a-0 Spike Plan

## Goal

Prove the minimum viable provenance-tag path by instrumenting the existing
`indicator.ewm` recipe expansion only.

## Non-Goals

- No new primitive token
- No new recipe
- No TagSpec registry
- No semantic_tag_hash
- No recipe generator
- No CSE/runtime cache
- No kernel substitution

## Proposed File Changes

- Add a minimal immutable `ProvenanceTag`.
- Add optional `provenance` metadata to graph/primitive nodes.
- Inject provenance only when compiling `indicator.ewm`.
- Preserve provenance through canonicalize rename / DCE / topological sort.
- Explicitly keep provenance out of graph, param, and instance hash material.
- Add agent-level explain folding for `indicator.ewm v1`.
- Add `strategies/uses_ewm_with_provenance.qst.yaml` using only existing tokens.

## ProvenanceTag Minimum Schema

```json
{
  "semantic_id": "indicator.ewm",
  "version": 1,
  "params": {"span": 3, "init": "first_value"},
  "role": "ewm",
  "tag_attached_by": "recipe_compiler"
}
```

`params` must be canonical JSON-stable data. Invalid values include NaN,
Infinity, bytes, tuple, non-string dict keys, custom objects, and nesting depth
greater than 8.

## Required Tests

- P0 `kdj_cross_basic` frozen hashes remain unchanged.
- P1 `examples_kdj_with_ema_filter` frozen hashes remain unchanged.
- `indicator.ewm` expansion carries provenance.
- Non-`indicator.ewm` recipes do not receive P2a-0 provenance.
- Canonicalize rename / DCE / sort preserves provenance on live nodes.
- Empty provenance is omitted from canonical serialization.
- Non-empty provenance does not affect hash material.
- `qst explain --level agent` folds tagged EWM primitive output as
  `indicator.ewm v1` without exposing `smooth.linear_recursive`.

## Hard Gate Commands

```bash
python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v
python -m pytest tests/e2e/test_p1_core_regression.py -v
python -m pytest tests/provenance -v
python -m pytest tests/e2e/test_p2a0_spike.py -v
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80
```

## Failure Handling

If provenance changes any P0/P1 hash or canonical graph identity, stop P2a-0 and
write a gate-failure ADR before continuing.
