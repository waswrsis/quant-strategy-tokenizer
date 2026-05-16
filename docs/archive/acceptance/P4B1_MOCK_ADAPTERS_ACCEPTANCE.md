# P4b-1 Mock Adapters + CLI Acceptance

Date: 2026-05-15

Implementation commit: `67ff4baeda5d6644dd950c5b6f7841e608c26e10`

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25891519847

Result: PASS

## Status

P4b-1 is accepted.

Implemented:

- Five local mock adapter entry points:
  - `mock-csv-market`
  - `mock-parquet-market`
  - `mock-backtest`
  - `mock-execution`
  - `mock-experiment`
- P4b CLI commands:
  - `qst load market`
  - `qst backtest`
  - `qst submit-plan`
  - `qst poll-execution`
  - `qst track`
  - `qst adapter list`
  - `qst adapter verify`

Not started:

- P4c external adapter repositories.
- Concrete vectorbt, ccxt, qlib, mlflow, broker, or exchange adapters.
- P4d semantic detokenize.

## Adapter Evidence

`qst adapter list` reports all five built-in mock adapters with deterministic ordering:

- `mock-backtest`
- `mock-csv-market`
- `mock-execution`
- `mock-experiment`
- `mock-parquet-market`

`qst adapter verify mock-execution` reports `execution=true`.

Unit coverage confirms:

- CSV and Parquet market adapters load P4 `MarketFrame` data.
- Symbol filtering is deterministic.
- Mock backtest output is deterministic for the same `SignalFrame`, `MarketFrame`, and config.
- Mock execution submit and poll return distinct immutable `ExecutionReport` artifacts.
- Mock experiment tracking returns a deterministic package `ArtifactRef`.

## CLI Evidence

Covered by `tests/cli/test_cli_p4b1.py`:

- `qst load market` writes canonical MarketFrame JSON with stable `frame_hash`.
- `qst backtest` builds a qstpkg and adds `BacktestEvidence` through the P4a-2 artifact extension.
- `qst verify <pkg>` passes after mock backtest artifact insertion.
- `qst submit-plan` writes a valid `ExecutionReport`.
- `qst poll-execution` writes a new valid `ExecutionReport`.
- `qst track` returns a deterministic `ArtifactRef`.

## Hash Preservation Evidence

`strategies/kdj_cross_basic.qst.yaml`:

- graph_hash: `sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947`
- param_hash: `sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28`
- instance_hash: `sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d`

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

`qst vocabulary --check` confirmed:

- P0 baseline preserved.
- Current vocabulary: 25 tokens, 9 recipes.

## Local Gate

Local checks before the implementation commit:

- `python -m pytest tests/adapters tests/ports -v`: PASS, 23 passed.
- `python -m pytest tests/cli -v`: PASS, 13 passed.
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v`: PASS, 8 passed.
- `python -m pytest tests/canonical_json tests/artifacts tests/e2e/test_p4a0_artifact_toy_e2e.py -v`: PASS, 46 passed.
- `python -m pytest tests/frames tests/package -v`: PASS, 76 passed.
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS.
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS.
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS.
- `python -m ruff check .`: PASS.
- `python -m mypy quant_strategy_tokenizer`: PASS.
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS.
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 449 passed, 89.72% coverage.

## CI Gate

GitHub Actions run `25891519847` passed:

- lint: PASS
- typecheck: PASS
- test on Python 3.11: PASS
- test on Python 3.12: PASS

## Boundary Confirmation

P4b-1 did not change:

- `qst execute` behavior, parameters, or trace semantics.
- Strategy IR schema, canonicalization, or three-layer hash rules.
- P3 lock/package/search/fork behavior.
- Mutation, CSE, fingerprint, or kernel substitution behavior.
- P0/P1/P2/P3/P4a accepted baselines.

The adapters are mock-only and local-only. They do not perform network access and do not claim numerical equivalence with any external backtest, broker, exchange, or experiment platform.
