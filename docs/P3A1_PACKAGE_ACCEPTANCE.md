# P3a-1 Package Acceptance Record

Date: 2026-05-14
Implementation commit: `73d35283d1de420754d513d3c937f7b4ee7a800f`

## Status

P3a-1 package format accepted.

Implemented scope:

- Directory package format `.qstpkg`.
- `qst package`.
- `qst unpack`.
- Package-aware `qst verify <pkg_dir>`.
- `agent.package()`.
- `agent.unpack()`.
- `agent.verify_package()`.
- `docs/JSON_SCHEMAS/qst_package_manifest.schema.json`.
- Package verification with `STRUCTURAL` and `SEMANTIC_TRACE` levels.

Deferred scope:

- P3b search index.
- P3b fork lineage and `qst-ir/0.3.1` output.
- Non-strict qst version policy.
- Numerical output equivalence verification.
- Zip or tar archive packaging.

## Package Layout

P3a-1 packages are directory packages, not archives.

Required files:

- `manifest.yaml`
- `qst.lock`
- `strategies/source.qst.yaml`
- `strategies/canonical.json`
- `fixtures/manifest.yaml`

Optional files:

- `fixtures/market.csv`
- `fixtures/expected_trace.json`
- `deps/tagspecs/*.yaml`
- `deps/recipes/*.json`

The package manifest is YAML. The lock file remains canonical JSON only.

## Local Checks

- `python -m pytest tests/package -v`: PASS, 14 tests
- `python -m pytest tests/e2e/test_p3a1_package_roundtrip.py -v`: PASS
- `python -m pytest tests/e2e/test_no_auto_ir_upgrade.py -v`: PASS
- `python -m pytest tests/qst_lock -v`: PASS, 20 tests
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS, 5 tests
- `python -m pytest tests/e2e/test_p1_core_regression.py -v`: PASS, 6 tests
- `python -m pytest tests/provenance tests/composition tests/execution tests/mutation -v`: PASS, 87 tests
- `python -m quant_strategy_tokenizer.cli package strategies/uses_ewm_with_provenance.qst.yaml --output $env:TEMP/uses_ewm.qstpkg`: PASS
- `python -m quant_strategy_tokenizer.cli verify $env:TEMP/uses_ewm.qstpkg`: PASS, `verification_level=STRUCTURAL`
- `python -m quant_strategy_tokenizer.cli unpack $env:TEMP/uses_ewm.qstpkg --output $env:TEMP/uses_ewm_unpacked`: PASS
- `python -m quant_strategy_tokenizer.cli package strategies/examples_kdj_with_ema_filter.qst.yaml --output $env:TEMP/examples_kdj.qstpkg --market examples/sample_market_btc_15m.csv --expected-trace $env:TEMP/qst_p3a1_expected_trace.json`: PASS
- `python -m quant_strategy_tokenizer.cli verify $env:TEMP/examples_kdj.qstpkg`: PASS, `verification_level=SEMANTIC_TRACE`
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 275 tests, 88.28% coverage

## CI

GitHub Actions run for implementation commit: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25874801564
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

The CI test job explicitly runs:

```bash
python -m pytest tests/package tests/e2e/test_p3a1_package_roundtrip.py -v
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

## Verification Evidence

- Untampered package without `fixtures/expected_trace.json` returns `VerifyResult(ok=True, verification_level=STRUCTURAL, failures=[])`.
- Untampered package with `fixtures/expected_trace.json` returns `VerifyResult(ok=True, verification_level=SEMANTIC_TRACE, failures=[])`.
- Tampered market fixture returns `market_csv_hash_mismatch`.
- Tampered expected trace returns trace hash mismatch failures.
- Tampered canonical JSON returns `canonical_ir_tampered`.
- Inconsistent surface strategy and canonical JSON returns `surface_canonical_inconsistent`.
- Missing manifest files return package manifest failures.
- `qst package`, `qst unpack`, and `qst verify` do not rewrite `qst-ir/0.3` to `qst-ir/0.3.1`.

## Boundary

P3a-1 is accepted as a package format and package verification stage only. Search, fork lineage, `qst-ir/0.3.1`, and numerical output equivalence remain not started.
