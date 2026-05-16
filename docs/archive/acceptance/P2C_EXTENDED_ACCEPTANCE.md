# P2c-extended Acceptance Record

Date: 2026-05-14
Implementation commit: `5f75cb5b9c3813808fe85cf42bb264e2a52c6576`

## Status

P2c-extended kernel substitution spike accepted.

Implemented scope:

- `KernelBinding`, `KernelRegistry`, and kernel eligibility report.
- One opt-in spike kernel for `indicator.ewm/v1`.
- `qst kernel plan`.
- `qst execute --kernel-substitution`.
- `agent.kernel_plan()` and opt-in agent execution.
- Trace evidence fields: `kernel_substituted`, `kernel_id`, `semantic_id`.

Deferred scope:

- Production kernel framework.
- Additional kernel bindings.
- Kernel performance benchmarking.
- Kernel substitution as default runtime behavior.
- Kernel substitution in canonical IR, hash material, or fingerprint material.

## Local Checks

- `python -m pytest tests/e2e/test_p0_p1_backward_compat.py -v`: PASS
- `python -m pytest tests/e2e/test_p1_core_regression.py -v`: PASS
- `python -m pytest tests/provenance tests/composition tests/contracts tests/fuzzing tests/metamorphic -v`: PASS
- `python -m pytest tests/execution -v`: PASS
- `python -m pytest tests/mutation -v`: PASS
- `python -m quant_strategy_tokenizer.cli vocabulary --check`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli hash strategies/examples_kdj_with_ema_filter.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli tag verify docs/tagspecs/indicator.ewm.tagspec.yaml --level full`: PASS
- `python -m quant_strategy_tokenizer.cli kernel plan strategies/uses_ewm_with_provenance.qst.yaml`: PASS
- `python -m quant_strategy_tokenizer.cli execute strategies/uses_ewm_with_provenance.qst.yaml --market examples/sample_market_btc_15m.csv --kernel-substitution --trace-path $env:TEMP/qst_kernel_trace.json`: PASS
- `python -m ruff check .`: PASS
- `python -m mypy quant_strategy_tokenizer`: PASS
- `python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer`: PASS
- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`: PASS, 233 tests, 87.36% coverage

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25868124724
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

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

- `qst kernel plan strategies/uses_ewm_with_provenance.qst.yaml` reports one eligible node for `builtin.indicator_ewm_v1_fastpath`.
- Default execution has no `kernel_substituted=true` trace nodes.
- Opt-in execution has one `kernel_substituted=true` trace node with `semantic_id=indicator.ewm`.
- Opt-in execution output matches default execution output.
