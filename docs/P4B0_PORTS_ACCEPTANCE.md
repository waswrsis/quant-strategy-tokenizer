# P4b-0 Port Protocols + SignalExtractionPolicy Acceptance

Date: 2026-05-14

Implementation commit: `c7e578deb857e54ce66aa487957ee8005d2944de`

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25890288593

Result: PASS

## Status

P4b-0 is accepted.

Implemented:

- Universal port protocols for market data, features, backtests, execution, experiments, strategy packages, and RL interface stubs.
- `SignalExtractionPolicy` and `execute_to_signals()` for converting supported runtime outputs into `SignalFrame`.
- Local adapter discovery using the `quant_strategy_tokenizer.adapters` entry-point group.
- Explicit CI coverage for `tests/ports -v`.

Not started:

- P4b-1 mock adapters and CLI commands.
- Concrete external adapters.
- `qst load market`, `qst backtest`, `qst submit-plan`, or `qst poll-execution`.
- P4d semantic detokenize.

## Boundary Confirmation

P4b-0 did not change:

- `qst execute` behavior.
- Strategy IR schema, canonicalization, or three-layer hash rules.
- P3 lock/package/search/fork behavior.
- Mutation, CSE, fingerprint, or kernel substitution behavior.
- P0/P1/P2/P3/P4a accepted baselines.

`BacktestPort` remains a signal-level protocol: it accepts `SignalFrame`, `MarketFrame`, and config. It does not import or accept `StrategyIR`.

Adapter discovery is local-only. No network registry, remote adapter lookup, or concrete adapter implementation was added.

## Signal Extraction Evidence

Covered by `tests/ports`:

- `Decision` output converts to `SignalFrame`.
- `Plan` output converts to `SignalFrame`.
- Boolean time series converts to long/flat signals.
- Numeric score time series converts only when `score_threshold` is set.
- Pure numeric time series without threshold raises `TypeError`.
- Failed runtime execution raises `RuntimeError`.
- Multi-symbol `MarketFrame` produces sorted long-format `SignalFrame`.
- `run_strategy_backtest()` calls `execute_to_signals()` before `BacktestPort.run_signals_backtest()`.

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

- `python -m pytest tests/ports -v`: PASS, 17 passed.
- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/e2e/test_p2_p3_backward_compat.py -v`: PASS, 8 passed.
- `python -m pytest tests/canonical_json tests/artifacts tests/e2e/test_p4a0_artifact_toy_e2e.py -v`: PASS, 46 passed.
- `python -m pytest tests/frames tests/package -v`: PASS, 76 passed.
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS.
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS.
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS.
- `python -m ruff check .`: PASS.
- `python -m mypy quant_strategy_tokenizer`: PASS.
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS.
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 438 passed, 89.50% coverage.

## CI Gate

GitHub Actions run `25890288593` passed:

- lint: PASS
- typecheck: PASS
- test on Python 3.11: PASS
- test on Python 3.12: PASS

The CI workflow explicitly runs:

```bash
python -m pytest tests/ports -v
```

## Known Limitations

P4b-0 intentionally stops at protocols, signal extraction, and local discovery primitives. It does not prove external adapter behavior, broker semantics, backtest engine equivalence, or numerical execution equivalence.
