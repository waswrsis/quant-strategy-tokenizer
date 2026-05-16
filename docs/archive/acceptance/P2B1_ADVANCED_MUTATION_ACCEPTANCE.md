# P2b-1 Advanced Mutation Acceptance Record

Date: 2026-05-14
Implementation commit: `b53c117663bb7ec41bfafef8e226e85f7363c838`

## Status

P2b-1 advanced mutation accepted.

Implemented scope:

- `ReplaceToken` mutation op.
- `InlineRecipe` mutation op.
- Type-compatible token replacement checks.
- Recipe output-preserving inlining.
- CLI support through existing `qst mutate --op`.
- Agent API support through existing `agent.mutate()`.

Deferred scope:

- Kernel substitution.
- New primitive tokens.
- New recipe generators.
- Automatic selection of replacement tokens.
- Multi-op transactions.

## Local Checks

- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/e2e/test_p1_core_regression.py -v`: PASS
- `python -m pytest tests/provenance tests/composition tests/contracts tests/fuzzing tests/metamorphic tests/execution tests/mutation -v`: PASS
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli tag verify docs/tagspecs/indicator.ewm.tagspec.yaml --level full`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 222 tests, 87.04% coverage

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25866790465
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

## Mutation Semantics

`ReplaceToken`:

- Applies only to surface graph nodes.
- Requires used output ports to exist on the replacement token with the same type.
- Rebuilds inputs by same-name ports or explicit `input_mapping`.
- Carries compatible preserved params plus explicit `new_params`.
- Emits before/after hashes and does not modify files unless `qst mutate --output` is used.

`InlineRecipe`:

- Applies to one surface recipe instance.
- Compiles the recipe to primitive graph nodes.
- Rewrites `recipe_id.port` and single-output `recipe_id` references.
- Removes only the inlined recipe instance.
- Preserves canonical hash semantics when inlining is semantically equivalent.

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

P2b-1 adds advanced mutation operations only. It does not change canonicalization, hash material, token vocabulary, recipe vocabulary, CSE behavior, or kernel substitution policy.
