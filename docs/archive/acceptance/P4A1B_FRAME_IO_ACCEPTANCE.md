# P4a-1b Frame IO Extras Acceptance

Date: 2026-05-14

Implementation commit: `b988d7930d33b433807823e9f2e80f6d632543ab`

CI run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25887145046

CI result: PASS

## Status

P4a-1b Frame IO Extras accepted.

P4a-1c strict alignment, P4a-2 qstpkg artifacts, P4b ports/adapters, and P4d semantic detokenize are not started.

## Scope Confirmed

- Added pandas interop for QST frames.
- Added Arrow Table interop for QST frames.
- Added Parquet read/write helpers for QST frames.
- Added optional dependency groups `pandas` and `parquet`.
- Added `pyarrow>=14` to dev dependencies so CI covers Arrow and Parquet behavior.
- DecimalString fields remain strings in pandas and Arrow; they are not converted to floats.
- Parquet round-trip acceptance is semantic `frame_hash` equality; Parquet byte equality is intentionally not required.
- Optional pyarrow import is guarded; module import remains safe without pyarrow and use raises an actionable `ImportError`.
- Did not add strict multi-symbol alignment, qstpkg artifact sections, port protocols, adapters, runtime signal extraction, or changes to `qst execute`.
- Did not change strategy canonicalization, strategy hashing, qst.lock, qstpkg verification, search, fork, mutation, CSE, or kernel behavior.

## Frame Hash Evidence

Toy MarketFrame:

```text
frame_hash:             sha256:4b2887c7d18e5df8509a07a0491d93228e5d95760e6576f97045ee1dc3bc981f
pandas_roundtrip_hash:  sha256:4b2887c7d18e5df8509a07a0491d93228e5d95760e6576f97045ee1dc3bc981f
arrow_roundtrip_hash:   sha256:4b2887c7d18e5df8509a07a0491d93228e5d95760e6576f97045ee1dc3bc981f
parquet_roundtrip_hash: sha256:4b2887c7d18e5df8509a07a0491d93228e5d95760e6576f97045ee1dc3bc981f
```

Toy FeatureFrame:

```text
frame_hash:             sha256:82124a257ad3524a113e1eac88866551e32f29c3c654c3f00cb4646da2d2b8d1
pandas_roundtrip_hash:  sha256:82124a257ad3524a113e1eac88866551e32f29c3c654c3f00cb4646da2d2b8d1
arrow_roundtrip_hash:   sha256:82124a257ad3524a113e1eac88866551e32f29c3c654c3f00cb4646da2d2b8d1
parquet_roundtrip_hash: sha256:82124a257ad3524a113e1eac88866551e32f29c3c654c3f00cb4646da2d2b8d1
```

Result: pandas, Arrow, and Parquet semantic round-trips preserve `frame_hash`.

## Backward Compatibility Evidence

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

Result: P0/P1/P2/P3/P4a-0/P4a-1a baselines preserved.

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

- `python -m pytest tests/frames -v`: 34 passed.
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: 393 passed, 89.45% coverage.
- `qst vocabulary --check`: 25 tokens, 9 recipes, P0 baseline preserved.

## CI Gate

GitHub Actions run `25887145046` passed:

- lint: PASS
- typecheck: PASS
- test Python 3.11: PASS
- test Python 3.12: PASS

CI explicitly runs `python -m pytest tests/frames -v`.

## Boundary

P4a-1b is limited to pandas, Arrow, and Parquet frame IO extras.

No strict alignment policy, qstpkg artifact extension, port protocol, concrete adapter, submit-plan, poll-execution, semantic detokenize, or runtime behavior change is included in this acceptance.
