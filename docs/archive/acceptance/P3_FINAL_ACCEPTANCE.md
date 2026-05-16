# P3 Final Acceptance Record

Date: 2026-05-14
Baseline commit before this final record: `7920acd54973c06182846f16dafc7d7d62f86a59`

## Status

P3 accepted.

Accepted stages:

- P3a-0 lock hard gate.
- P3a-1 package format.
- P3b-0 search and `IndexRecord`.
- P3b-1 fork lineage and `qst-ir/0.3.1`.

## Scope Accepted

P3 provides:

- deterministic canonical JSON `qst.lock`;
- structured `qst verify`;
- directory `.qstpkg` packaging, unpacking, and package verification;
- structural and trace-semantic verification levels;
- on-demand in-memory search over public token, recipe, and TagSpec registries;
- additive fork lineage metadata via `derived_from`;
- `qst fork` as the only command that emits `qst-ir/0.3.1`.

## Non-Scope

P3 does not provide:

- numerical output equivalence proof;
- persistent package search index files;
- P4+ full-text search;
- cross-package catalog search;
- automatic upgrade from `qst-ir/0.3` to `qst-ir/0.3.1`;
- changes to P0/P1/P2 token semantics, recipes, canonicalization, hashing, execution fingerprints, mutation semantics, or kernel behavior.

## Hash Preservation

`strategies/kdj_cross_basic.qst.yaml` remains:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml` remains:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

## Local Final Gate

The final local P3 gate was run before this record was committed:

- `python -m pytest tests/qst_lock tests/package tests/agent tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_p3a1_package_roundtrip.py tests/e2e/test_p3b0_search.py tests/e2e/test_p3b1_fork.py -v`: PASS
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/provenance tests/composition tests/execution tests/mutation -v`: PASS
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS
- `python -m quant_strategy_tokenizer.cli package strategies/uses_ewm_with_provenance.qst.yaml --output <temp>/uses_ewm.qstpkg`: PASS
- `python -m quant_strategy_tokenizer.cli verify <temp>/uses_ewm.qstpkg`: PASS
- `python -m quant_strategy_tokenizer.cli search tagspec --fully-verified`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 310 tests, 88.38% coverage

## CI Evidence

Latest P3 stage CI runs:

- P3b-0 implementation: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25876104394, PASS
- P3b-0 acceptance: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25876300094, PASS
- P3b-1 implementation: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25876916903, PASS
- P3b-1 acceptance: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25877113522, PASS

The final acceptance documentation commit must also pass the standard CI workflow before P3 is considered closed on `main`.

## Result

P3 is accepted as a structural packaging, verification, search, and lineage layer. P0/P1/P2 frozen behavior remains preserved.
