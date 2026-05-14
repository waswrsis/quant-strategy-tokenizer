# QST P2a-0 Spike Plan

## Goal

Prove the minimum viable provenance-tag path before P2 starts.

## Non-Goals

- No production provenance system
- No TagSpec registry
- No semantic_tag_hash
- No recipe generator
- No CSE/runtime cache
- No kernel substitution

## Proposed File Changes

- strategy IR model extension for optional provenance metadata
- canonicalize preservation test
- hashing ignore-provenance test
- explain fold tag test
- tagged example strategy

## ProvenanceTag Minimum Schema

Draft only:

```json
{
  "kind": "provenance",
  "source": "manual",
  "label": "stats.rolling_zscore",
  "note": "human-readable only"
}
```

## Required Tests

- hash ignores provenance
- canonicalize preserves provenance
- explain folds tag into readable output
- `stats.rolling_zscore` tagged example does not alter P0/P1 hash semantics

## Hard Gate Commands

```bash
python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v
python -m pytest tests/e2e/test_p1_core_regression.py -v
python -m pytest tests/e2e/test_p2a0_provenance_spike.py -v
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80
```

## Failure Handling

If provenance changes any P0/P1 hash or canonical graph identity, stop P2a-0 and write an ADR before continuing.
