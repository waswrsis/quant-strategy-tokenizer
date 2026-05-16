# P4a-1c Strict Market Alignment Acceptance

Date: 2026-05-14

Implementation commit: `34ff1952063293457d99599660febbe972244d28`

CI run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25888251161

CI result: PASS

## Status

P4a-1c Multi-Symbol Strict Alignment accepted.

P4a-2 qstpkg artifacts, P4b ports/adapters, and P4d semantic detokenize are not started.

## Scope Confirmed

- Added strict timestamp-symbol grid validation for `MarketFrame` OHLCV bars.
- Kept strict alignment limited to market data frames.
- Preserved sparse `SignalFrame` and `FeatureFrame` behavior.
- Preserved empty `MarketFrame(symbols=[], bars=[])`.
- Preserved single-symbol sparse timestamp support; no frequency inference was added.
- Preserved existing `compute_frame_hash()` material and excluded `frame_hash` as before.
- Did not add `allow_missing`, sparse market data support, nullable DecimalString fields, `time_range`, or `frequency`.
- Did not change `qst execute`, strategy canonicalization, strategy hashing, qst.lock, package verification, search, fork, mutation, CSE, or kernel behavior.

## Frame Hash Evidence

P4a-1b toy MarketFrame hash remains unchanged:

```text
sha256:4b2887c7d18e5df8509a07a0491d93228e5d95760e6576f97045ee1dc3bc981f
```

P4a-1b toy FeatureFrame hash remains unchanged:

```text
sha256:82124a257ad3524a113e1eac88866551e32f29c3c654c3f00cb4646da2d2b8d1
```

Result: P4a-1c strict alignment did not change accepted P4a-1b frame hash evidence.

## Backward Compatibility Evidence

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

Result: P0/P1/P2/P3/P4a-0/P4a-1a/P4a-1b baselines preserved.

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

Observed local results:

- `python -m pytest tests/frames -v`: 43 passed.
- `python -m pytest tests/canonical_json tests/artifacts tests/e2e/test_p4a0_artifact_toy_e2e.py -v`: 46 passed.
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v`: 8 passed.
- `python -m pytest tests/qst_lock tests/package tests/agent tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_p3a1_package_roundtrip.py tests/e2e/test_p3b0_search.py tests/e2e/test_p3b1_fork.py -v`: 65 passed.
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: 402 passed, 89.47% coverage.
- `qst vocabulary --check`: 25 tokens, 9 recipes, P0 baseline preserved.

## CI Gate

GitHub Actions run `25888251161` passed:

- lint: PASS
- typecheck: PASS
- test Python 3.11: PASS
- test Python 3.12: PASS

CI explicitly runs `python -m pytest tests/frames -v`.

## Boundary

P4a-1c is limited to strict OHLCV market frame alignment and frame hash stability coverage.

No qstpkg artifact extension, port protocol, adapter, submit-plan, poll-execution, semantic detokenize, runtime behavior change, or sparse market data policy is included in this acceptance.
