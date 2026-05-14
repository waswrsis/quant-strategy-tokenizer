# P2a-0 Gate Acceptance Record

Date: 2026-05-14
Commit: `1a18fb05310605a3db3f594c557d3542f1ca40e3`

## Status

P2a-0 hard gate passed for the `indicator.ewm` provenance spike.

## Local Checks

- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/e2e/test_p1_core_regression.py -v`: PASS
- `python -m pytest tests/provenance -v`: PASS
- `python -m pytest tests/e2e/test_p2a0_spike.py -v`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25861473017
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

## Gate Invariants

- P0 `kdj_cross_basic` graph_hash unchanged: PASS
- P0 `kdj_cross_basic` param_hash unchanged: PASS
- P0 `kdj_cross_basic` instance_hash unchanged: PASS
- P1-core `examples_kdj_with_ema_filter` graph_hash unchanged: PASS
- P1-core `examples_kdj_with_ema_filter` param_hash unchanged: PASS
- P1-core `examples_kdj_with_ema_filter` instance_hash unchanged: PASS
- Provenance omitted from hash material: PASS
- `qst explain --level agent` folds `indicator.ewm v1`: PASS

## Scope Confirmation

No primitive token, recipe, TagSpec, recipe generator, mutation engine, CSE/runtime cache, or kernel substitution was added in P2a-0.
