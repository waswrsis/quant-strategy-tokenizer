# P3b-1 Fork Acceptance Record

Date: 2026-05-14
Implementation commit: `a7604223e5b35fee7bddcfc229b6267885129109`

## Status

P3b-1 fork and lineage metadata accepted.

Implemented scope:

- Additive `qst-ir/0.3.1` support.
- Frozen `DerivedFrom` lineage metadata.
- `agent.fork()`.
- `qst fork`.
- Mutation-chain append for forked IR.
- CI explicit P3b-1 test step.

Deferred scope:

- Fork-time mutation application.
- Package lineage graph traversal.
- Search over lineage.
- Numerical equivalence verification.
- Any change to P0/P1/P2 canonical or hash algorithms.

## Local Checks

- `python -m pytest tests/e2e/test_no_auto_ir_upgrade.py -v`: PASS
- `python -m pytest tests/e2e/test_p3b1_fork.py -v`: PASS
- `python -m pytest tests/ir/test_derived_from.py tests/mutation/test_lineage_chain.py -v`: PASS
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/qst_lock tests/package tests/agent tests/e2e/test_p3b0_search.py -v`: PASS
- `python -m quant_strategy_tokenizer.cli fork strategies/kdj_cross_basic.qst.yaml --new-id kdj_variant --out <temp>/kdj_variant.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 310 tests, 88.38% coverage

## CI

GitHub Actions run for implementation commit: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25876916903
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

The CI test job explicitly runs:

```bash
python -m pytest tests/e2e/test_p3b1_fork.py tests/ir/test_derived_from.py tests/mutation/test_lineage_chain.py -v
```

## Hash Preservation

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

## Evidence

- Loader accepts both `qst-ir/0.3` and `qst-ir/0.3.1`.
- `qst-ir/0.3` with `derived_from` is rejected.
- `qst fork` writes YAML with `ir_version: qst-ir/0.3.1`.
- Parent IR remains unchanged after `agent.fork()`.
- `canonicalize()` carries `derived_from` inertly and does not auto-upgrade old IR.
- Three-layer strategy hashes ignore `derived_from`.
- Execution fingerprints ignore `derived_from`.
- Mutating `qst-ir/0.3` preserves `qst-ir/0.3` and does not add lineage.
- Mutating forked `qst-ir/0.3.1` appends the operation JSON to `derived_from.mutation_chain`.

## Boundary

`qst fork` and `agent.fork()` are the only P3b-1 paths that intentionally emit `qst-ir/0.3.1`. Existing commands continue preserving `qst-ir/0.3`. Lineage is inert metadata and is excluded from validation semantics, execution behavior, trace semantics, graph/param/instance hash material, and execution fingerprint material.
