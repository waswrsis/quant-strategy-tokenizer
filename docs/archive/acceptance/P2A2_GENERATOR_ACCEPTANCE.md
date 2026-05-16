# P2a-2 Generator Acceptance Record

Date: 2026-05-14
Implementation commit: `0f2184a75d7fb2eb7355013a4417f48bc42a5d7d`

## Status

P2a-2 recipe generator accepted.

Implemented scope:

- Deterministic YAML generator DSL.
- Hard constraint checks for node count, static loop size, include depth, recursive include, path escape, URL include, and nondeterministic constructs.
- Built-in generator source for `signals.dual_ema_cross/v1`.
- Built-in generated recipe artifact for `signals.dual_ema_cross/v1`.
- `qst recipe expand`.
- `agent.recipe_expand()`.
- `docs/JSON_SCHEMAS/generator.schema.json`.

Deferred scope:

- P2a-3 composition validation.
- Full algorithm recipe library.
- Fully verified TagSpec upgrade for generated recipes.
- P2b-1 advanced mutation.
- P2c-extended kernel substitution.

## Local Checks

- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/e2e/test_p1_core_regression.py -v`: PASS
- `python -m pytest tests/provenance -v`: PASS
- `python -m pytest tests/mutation -v`: PASS
- `python -m pytest tests/execution -v`: PASS
- `python -m pytest tests/composition -v`: PASS
- `python -m pytest tests/recipes -v`: PASS
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS
- `python -m quant_strategy_tokenizer.cli recipe expand signals.dual_ema_cross --params '{"fast_span":9,"slow_span":21}' --output "$env:TEMP/dual_ema_cross.json"`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 203 tests, 87.27% coverage

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25864965346
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

## Vocabulary

- P0 frozen baseline: 17 tokens, 4 recipes, preserved.
- P1-core baseline: 25 tokens, 8 recipes, preserved.
- Current vocabulary: 25 tokens, 9 recipes.
- New P2a-2 recipe: `signals.dual_ema_cross/v1`.
- New primitive tokens: none.

## Hash Preservation

P0 `strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

P1-core `strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

## Scope Confirmation

P2a-2 adds deterministic recipe generation and one algorithm recipe only. It does not add a primitive token, kernel, recipe generator runtime execution, P2a-3 composition validation, advanced mutation, or kernel substitution.
