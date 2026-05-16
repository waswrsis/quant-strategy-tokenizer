# P2a-3 Composition Validation Acceptance Record

Date: 2026-05-14
Implementation commit: `32ad8b67d65363f0c057e850135b295d4b77bcd7`

## Status

P2a-3 composition validation accepted.

Implemented scope:

- Recipe contract framework.
- Deterministic `ci_standard` reference fuzzing harness.
- Metamorphic property runner.
- `upgrade_verification()` for progressive TagSpec verification.
- `qst tag verify --level full`.
- `agent.tagspec_verify(..., level="full")`.
- Full verification for `indicator.ewm/v1`.

Deferred scope:

- P2b-1 advanced mutation.
- P2c-extended kernel substitution.
- Fully verified TagSpec for `signals.dual_ema_cross/v1`.
- Expanded algorithm recipe library.
- Formal proof of recipe equivalence.

## Local Checks

- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/e2e/test_p1_core_regression.py -v`: PASS
- `python -m pytest tests/provenance -v`: PASS
- `python -m pytest tests/composition -v`: PASS
- `python -m pytest tests/contracts -v`: PASS
- `python -m pytest tests/fuzzing -v`: PASS
- `python -m pytest tests/metamorphic -v`: PASS
- `python -m pytest tests/e2e/test_p2a3_composition_validation.py -v`: PASS
- `python -m quant_strategy_tokenizer.cli tag verify docs/tagspecs/indicator.ewm.tagspec.yaml --level full`: PASS
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 215 tests, 86.89% coverage

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25866040461
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

## Verification Evidence

`docs/tagspecs/indicator.ewm.tagspec.yaml`:

- minimally_attached: true
- contracts_pass: true
- fuzzing_at_ci_standard: true
- metamorphic_pass: true
- fully_verified: true

Stored artifacts:

- Contract suite: `docs/contracts/indicator.ewm.contracts.yaml`
- Fuzzing report: `docs/fuzzing/indicator.ewm.ci_standard.json`

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

P2a-3 full verification is empirical, not formal. It does not change P0/P1 hash material, canonicalization, primitive vocabulary, algorithm recipe vocabulary, advanced mutation, or kernel substitution policy.
