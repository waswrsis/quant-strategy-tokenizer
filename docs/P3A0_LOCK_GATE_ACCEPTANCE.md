# P3a-0 Lock Gate Acceptance Record

Date: 2026-05-14
Implementation commit: `da55214508e00899e3d3f8c57e4c3ab1e9a36f6f`

## Status

P3a-0 lock hard gate accepted.

Implemented scope:

- Deterministic canonical JSON `qst.lock`.
- `qst lock`.
- `qst verify`.
- `agent.lock()`.
- `agent.verify()`.
- `docs/JSON_SCHEMAS/qst_lock.schema.json`.
- Structured `VerifyResult` with `verification_level` and `limitation_note`.
- Hard-gate tamper failures for instance hash, fixtures, canonical IR, version policy, and TagSpec verification state.

Deferred scope:

- P3a-1 package format.
- P3b search index.
- P3b fork lineage and `qst-ir/0.3.1` output.
- Non-strict qst version policy.
- Numerical output equivalence verification.

## Local Checks

- `python -m pytest tests/qst_lock -v`: PASS
- `python -m pytest tests/e2e/test_p3a0_lock_spike.py -v`: PASS
- `python -m pytest tests/e2e/test_no_auto_ir_upgrade.py -v`: PASS
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/e2e/test_p1_core_regression.py -v`: PASS
- `python -m pytest tests/provenance tests/composition tests/execution tests/mutation -v`: PASS
- `python -m quant_strategy_tokenizer.cli lock strategies/uses_ewm_with_provenance.qst.yaml --output $env:TEMP/qst.lock --canonical-output $env:TEMP/qst.canonical.json`: PASS
- `python -m quant_strategy_tokenizer.cli verify strategies/uses_ewm_with_provenance.qst.yaml --lock $env:TEMP/qst.lock --canonical $env:TEMP/qst.canonical.json`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 258 tests, 87.19% coverage

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25873739056
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

The CI test job explicitly runs:

```bash
python -m pytest tests/qst_lock tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_no_auto_ir_upgrade.py -v
```

## Hash Preservation

P0 `strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

P1-core `strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

## Evidence

- Re-running `qst lock` on `strategies/uses_ewm_with_provenance.qst.yaml` produces byte-identical lock output.
- `qst verify` returns `VerifyResult(ok=True, verification_level=STRUCTURAL, failures=[])` for an untampered lock.
- Tampered `instance_hash` returns `instance_hash_mismatch`.
- Tampered market CSV fixture returns `market_csv_hash_mismatch`.
- Tampered canonical IR returns `canonical_ir_tampered`.
- Inconsistent surface/canonical pair returns `surface_canonical_inconsistent`.
- `qst_version_policy=same_minor` returns `qst_version_policy_unsupported`.
- P3a-0 commands do not rewrite `qst-ir/0.3` to `qst-ir/0.3.1`.

## Boundary

P3a-0 is accepted as a lock hard gate only. Package, search, fork lineage, and `qst-ir/0.3.1` remain not started.
