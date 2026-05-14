# P4a-2 qstpkg Artifacts Extension Acceptance

Date: 2026-05-14

Implementation commit: `895774d71b3944547ec94667c7816e01479c93b6`

CI run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25889277676

CI result: PASS

## Status

P4a-2 qstpkg Artifacts Extension accepted.

P4b ports/adapters, P4d semantic detokenize, submit-plan, and poll-execution are not started.

## Scope Confirmed

- Added an optional `artifacts` section to P3 `.qstpkg` manifests.
- Preserved `package_version: qstpkg/0.1`.
- Preserved old packages with no `artifacts` section; they still parse and verify.
- Added package helpers for adding P4 artifact JSON files to a package.
- Added `qst pkg add-artifact` and `qst pkg verify-artifacts`.
- Extended `qst verify <pkg_dir>` to include artifact checks automatically.
- Extended `docs/JSON_SCHEMAS/qst_package_manifest.schema.json` additively.
- Did not change P3 `qst.lock` bytes, lock schema, strategy hashes, runtime execution, mutation, search, fork, CSE, or kernel behavior.

## Artifact Manifest Evidence

The optional manifest section supports:

- `backtest.evidence`
- `backtest.files`
- `execution.reports`
- `execution.raw_payloads`
- `portfolio.snapshots`

Path safety is enforced through POSIX relative path validation:

- absolute paths rejected
- `..` paths rejected
- backslash paths rejected

Legacy P3 package manifests without `artifacts` remain valid under both Pydantic model validation and the draft 2020-12 package manifest schema.

## Package Verification Evidence

Artifact verification covers:

- artifact JSON file existence
- artifact JSON file hash consistency
- package manifest tracking for primary artifact JSON files
- `ExecutionReport.raw_payload_ref` / `raw_payload_hash` existence and hash match
- `BacktestEvidence` internal `ArtifactRef` existence and hash match
- malformed or unknown artifact JSON failure paths

Observed structured failures include:

- `artifact_file_missing`
- `artifact_file_hash_mismatch`
- `artifact_raw_payload_hash_mismatch`
- `artifact_ref_missing`
- `artifact_ref_hash_mismatch`
- `artifact_json_invalid`
- `artifact_file_untracked`

## Backward Compatibility Evidence

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

Result: P0/P1/P2/P3/P4a-0/P4a-1a/P4a-1b/P4a-1c baselines preserved.

## Local Gate

All local checks passed before commit:

```bash
python -m pytest tests/package -v
python -m pytest tests/e2e/test_p3a1_package_roundtrip.py -v
python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v
python -m pytest tests/canonical_json tests/artifacts tests/e2e/test_p4a0_artifact_toy_e2e.py -v
python -m pytest tests/frames -v
python -m pytest tests/qst_lock tests/package tests/agent tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_p3a1_package_roundtrip.py tests/e2e/test_p3b0_search.py tests/e2e/test_p3b1_fork.py -v
python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml
python -m quant_strategy_tokenizer.cli vocabulary --check
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80
```

Observed local results:

- `python -m pytest tests/package -v`: 33 passed.
- `python -m pytest tests/e2e/test_p3a1_package_roundtrip.py -v`: 2 passed.
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v`: 8 passed.
- `python -m pytest tests/canonical_json tests/artifacts tests/e2e/test_p4a0_artifact_toy_e2e.py -v`: 46 passed.
- `python -m pytest tests/frames -v`: 43 passed.
- `python -m pytest tests/qst_lock tests/package tests/agent tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_p3a1_package_roundtrip.py tests/e2e/test_p3b0_search.py tests/e2e/test_p3b1_fork.py -v`: 84 passed.
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: 421 passed, 89.44% coverage.
- `qst vocabulary --check`: 25 tokens, 9 recipes, P0 baseline preserved.

## CI Gate

GitHub Actions run `25889277676` passed:

- lint: PASS
- typecheck: PASS
- test Python 3.11: PASS
- test Python 3.12: PASS

CI explicitly ran P0 backward compatibility, P2/P3 backward compatibility, P4a-0 artifact tests, frame tests, qst lock tests, package tests, search/fork tests, and the full coverage gate.

## Boundary

P4a-2 is limited to additive package artifact manifest support and artifact verification.

No port protocol, concrete adapter, submit-plan, poll-execution, semantic detokenize, runtime behavior change, strategy hash change, qst.lock schema change, or qstpkg package version bump is included in this acceptance.
