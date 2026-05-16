# P4a-0 Artifact Schema Hard Gate Acceptance

Date: 2026-05-14

Implementation commit: `8139894d834ded7880a2a5b3ca4a15d5316abec9`

CI run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25884951020

CI result: PASS

## Status

P4a-0 artifact schema hard gate accepted.

P4a-1 frame, P4a-2 qstpkg artifact extension, P4b ports/adapters, and P4d semantic detokenize are not started.

## Scope Confirmed

- Public `stable_json_bytes()` added in `quant_strategy_tokenizer/canonical_json.py`.
- P3 `canonical_lock_bytes()` remains a thin wrapper over byte-compatible canonical JSON.
- Five draft 2020-12 JSON Schemas added and validated:
  - `artifact_base.schema.json`
  - `execution_report.schema.json`
  - `backtest_evidence.schema.json`
  - `portfolio_snapshot.schema.json`
  - `adapter_manifest.schema.json`
- P4 artifact base models added:
  - `ExecutionReport`
  - `BacktestEvidence`
  - `PortfolioSnapshot`
  - `AdapterManifest`
- Artifact IDs are deterministic and exclude `artifact_id` and `metadata`.
- `qst-execution-report/1` artifact ID excludes `raw_payload_ref` and includes `raw_payload_hash`.
- POSIX relative path rules enforced for artifact refs and raw payload refs.
- Adapter manifest version fields use PEP 440 validation.
- P4a-0 does not change `qst execute`, strategy canonicalization, strategy hashing, lock verification, package verification, search, fork, mutation, CSE, or kernel behavior.

## DecimalString Gate

- Strict DecimalString fields reject non-canonical values such as `1.0`, `1.00`, `0.10`, `0.50`, `1e-3`, `+1.0`, `001.0`, and `-0`.
- Normalization maps raw negative zero inputs to canonical `0`:
  - `normalize_to_canonical("-0") == "0"`
  - `normalize_to_canonical(Decimal("-0.000")) == "0"`
- Pre-flight fixture scan found decimal-looking strings only in non-P4 artifact fixture contexts; no migration was required.

## Hash Preservation

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

Result: P0/P1/P2/P3 hash baselines preserved.

## Local Gate

All local checks passed before commit:

```bash
python -m pytest tests/canonical_json tests/artifacts tests/e2e/test_p4a0_artifact_toy_e2e.py -v
python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v
python -m pytest tests/qst_lock tests/package tests/agent tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_p3a1_package_roundtrip.py tests/e2e/test_p3b0_search.py tests/e2e/test_p3b1_fork.py -v
python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml
python -m quant_strategy_tokenizer.cli vocabulary --check
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80
```

Full coverage result: 359 passed, 88.80% coverage.

## CI Gate

GitHub Actions run `25884951020` passed:

- lint: PASS
- typecheck: PASS
- test Python 3.11: PASS
- test Python 3.12: PASS

CI explicitly runs:

- P0 backward compatibility
- P2/P3 backward compatibility
- P4a-0 canonical JSON, artifact schema, and toy e2e tests
- P3 lock/package/search/fork regression tests
- full coverage gate

## Boundary

P4a-0 is a schema and identity hard gate only.

No concrete adapter, frame model, package artifact extension, submit-plan, poll-execution, or semantic detokenize feature is included in this acceptance.
