# P4a-1a Frame Model Minimal Acceptance

Date: 2026-05-14

Implementation commit: `16a6701a060c0958933b37ae522f8601710d01d8`

CI run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25886142157

CI result: PASS

## Status

P4a-1a Frame Model Minimal accepted.

P4a-1b Parquet/Arrow/pandas IO, P4a-1c strict multi-symbol alignment, P4a-2 qstpkg artifacts, P4b ports/adapters, and P4d semantic detokenize are not started.

## Scope Confirmed

- Added `quant_strategy_tokenizer.frames`.
- Added `MarketFrame`, `SignalFrame`, `FeatureFrame`, and `TraceLog`.
- Added long-format `OHLCVBar`, signal rows, feature rows, and trace events.
- Added `compute_frame_hash(frame)` using public `stable_json_bytes()`.
- Added canonical JSON IO and stdlib CSV IO.
- Reused P4a-0 `DecimalString` for OHLCV, signal size, and feature values.
- Did not add pandas, pyarrow, Parquet, adapters, qstpkg artifact sections, or runtime signal extraction.
- Did not change `qst execute`, strategy canonicalization, strategy hashing, P3 lock/package/search/fork behavior, mutation, CSE, or kernel behavior.

## Frame Hash Evidence

Toy MarketFrame:

```text
frame_hash: sha256:e770b6985d35a8254248d39a0f855f10c41909f20146059c741169d1e6015138
json_roundtrip_hash: sha256:e770b6985d35a8254248d39a0f855f10c41909f20146059c741169d1e6015138
csv_roundtrip_hash:  sha256:e770b6985d35a8254248d39a0f855f10c41909f20146059c741169d1e6015138
```

Result: JSON and CSV semantic round-trip preserve `frame_hash`.

## Backward Compatibility Evidence

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

Result: P0/P1/P2/P3/P4a-0 baselines preserved.

## Local Gate

All local checks passed before commit:

```bash
python -m pytest tests/frames -v
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

Full coverage result: 385 passed, 89.28% coverage.

## CI Gate

GitHub Actions run `25886142157` passed:

- lint: PASS
- typecheck: PASS
- test Python 3.11: PASS
- test Python 3.12: PASS

CI explicitly runs `python -m pytest tests/frames -v`.

## Boundary

P4a-1a is limited to JSON/CSV minimal frame models and deterministic frame hashes.

No strict multi-symbol completeness validation, Parquet/Arrow/pandas IO, qstpkg artifacts integration, port protocol, adapter, submit-plan, poll-execution, or semantic detokenize feature is included in this acceptance.
