# P4-Core Acceptance Record

Date: 2026-05-15

Accepted implementation baseline: `3c8bb7f454ce01cb438c1b3d4be93946eff3a536`

Acceptance record: the commit that adds this file.

## Status

P4-core is accepted.

Accepted stages:

- P4a-0 Artifact Schema Hard Gate
- P4a-1a Frame Model Minimal
- P4a-1b Frame I/O Extras
- P4a-1c Multi-symbol Strict Alignment
- P4a-2 qstpkg Artifacts Extension
- P4b-0 Port Protocols + SignalExtractionPolicy
- P4b-1 Mock Adapters + CLI

## Accepted Scope

P4-core adds the universal artifact, frame, package-artifact, port, and mock-adapter layer.

Included:

- Artifact schemas and identity for execution reports, backtest evidence, portfolio snapshots, and adapter manifests.
- Strict DecimalString validation and canonical artifact JSON.
- Market, signal, feature, and trace frames with JSON, CSV, pandas, Arrow, and Parquet round trips.
- Strict multi-symbol MarketFrame alignment.
- Additive qstpkg artifact references and verification.
- Universal Port protocols and `execute_to_signals()`.
- Five local mock adapters and P4b CLI commands.

Not included:

- P4c real adapter repositories.
- P4d semantic detokenize.
- MCP.
- Production broker or exchange integrations.
- Numerical equivalence proof.
- Changes to `qst execute`.
- Changes to P0/P1/P2/P3 canonicalization, hashing, lock, package, search, fork, mutation, CSE, or kernel behavior.

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

## Mock Adapter CLI Evidence

`qst adapter list` reports all five built-in mock adapters with deterministic ordering:

- `mock-backtest`
- `mock-csv-market`
- `mock-execution`
- `mock-experiment`
- `mock-parquet-market`

`qst adapter verify mock-execution` reports:

- `ok: true`
- `execution: true`
- `market_data: false`
- `backtest: false`
- `experiment: false`

P4b CLI coverage confirms:

- `qst load market` writes canonical MarketFrame JSON.
- `qst backtest` builds a qstpkg and inserts BacktestEvidence through the P4a-2 artifact extension.
- `qst submit-plan` writes a valid ExecutionReport.
- `qst poll-execution` writes a distinct valid ExecutionReport.
- `qst track` returns a deterministic ArtifactRef.
- `qst verify <pkg_dir>` validates package artifacts.

## Local Final Gate

All local final checks passed on 2026-05-15:

- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v`: PASS, 8 passed.
- `python -m pytest tests/canonical_json tests/artifacts tests/e2e/test_p4a0_artifact_toy_e2e.py -v`: PASS, 46 passed.
- `python -m pytest tests/frames tests/package tests/ports tests/adapters tests/cli -v`: PASS, 112 passed.
- `python -m pytest tests/qst_lock tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_no_auto_ir_upgrade.py -v`: PASS, 25 passed.
- `python -m pytest tests/agent tests/e2e/test_p3b0_search.py tests/e2e/test_p3b1_fork.py -v`: PASS, 27 passed.
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS.
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS.
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS.
- `python -m quant_strategy_tokenizer.cli adapter list`: PASS.
- `python -m quant_strategy_tokenizer.cli adapter verify mock-execution`: PASS.
- `python -m ruff check .`: PASS.
- `python -m mypy quant_strategy_tokenizer`: PASS.
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS.
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 449 passed, 89.72% coverage.

The coverage run emitted a non-blocking coverage parse warning for `quant_strategy_tokenizer/package/manifest.py`; the command exited 0 and coverage remained above the required threshold.

## CI Evidence

Latest P4b-1 acceptance CI before this final record:

- GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25891708451
- Result: PASS

The P4-core acceptance commit must also pass GitHub Actions before P4-core is considered operationally closed.

## Result

P4-core is accepted as the artifact/frame/package-artifact/port/mock-adapter layer.

P4c real adapters and P4d semantic detokenize remain explicitly not started.
