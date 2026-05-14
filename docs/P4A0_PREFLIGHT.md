# P4a-0 Pre-flight Record

Date: 2026-05-14
Baseline commit: `07ef24b`

## Status

P4a-0 pre-flight completed. P4a-0 code construction may start after this record is committed and CI passes.

## Manual Clarifications Applied

- P4a-0 gate item 1 validates five JSON schemas:
  - `artifact_base.schema.json`
  - `execution_report.schema.json`
  - `backtest_evidence.schema.json`
  - `portfolio_snapshot.schema.json`
  - `adapter_manifest.schema.json`
- `DecimalString` rejects `"-0"`.
- `normalize_to_canonical("-0")` and `normalize_to_canonical(Decimal("-0.000"))` must return `"0"`.
- The mypy command remains the current accepted CI baseline: `python -m mypy quant_strategy_tokenizer`.
- Upgrading to `mypy --strict` as a command-line gate is out of scope for P4a-0 and requires a separate hardening PR.

## DecimalString Fixture Scan

Command:

```bash
python <read-only decimal candidate scanner>
```

Results:

```text
examples/sample_market_btc_15m.csv: 5 candidates
docs/contracts/indicator.ewm.contracts.yaml: 14 candidates
docs/fuzzing/indicator.ewm.ci_standard.json: 1 candidate
TOTAL_FILES 3
TOTAL_MATCHES 20
```

Assessment:

- `examples/sample_market_btc_15m.csv` is a P0/P1/P2/P3 market CSV fixture consumed as pandas numeric data, not a P4 artifact `DecimalString` field.
- `docs/contracts/indicator.ewm.contracts.yaml` is a composition contract fixture, not a P4 artifact `DecimalString` field.
- `docs/fuzzing/indicator.ewm.ci_standard.json` is a fuzzing report fixture, not a P4 artifact `DecimalString` field.
- No migration is required before P4a-0 code construction.
- No frozen hash baseline is updated.

## Backward Compatibility Checks

P2/P3 regression command:

```bash
python -m pytest tests/e2e/test_p0_p1_backward_compat.py tests/qst_lock tests/package tests/agent tests/e2e/test_p3a0_lock_spike.py tests/e2e/test_p3a1_package_roundtrip.py tests/e2e/test_p3b0_search.py tests/e2e/test_p3b1_fork.py -q
```

Result:

```text
70 passed
```

P0/P1 hash smoke:

```text
strategies/kdj_cross_basic.qst.yaml
graph_hash:    sha256:2b84dcdcebf5af4d2bab65c872745b1d9ec872d181f69944e7ad3d9371d65947
param_hash:    sha256:3b5e14a46a17204bb5b771d339f4fc660f1e059755c0184a17f13312fb471c28
instance_hash: sha256:5cb1fe6e4d8ba9dd2230b4654e4cdb8411143c90ad1bcb5eb18fcb8c421ec85d

strategies/examples_kdj_with_ema_filter.qst.yaml
graph_hash:    sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa
param_hash:    sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321
instance_hash: sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3
```

## P4a-0 Start Conditions

- P4 ADR exists: PASS
- DecimalString fixture scan complete: PASS
- No fixture migration required: PASS
- P0/P1/P2/P3 regression entrypoint confirmed: PASS
- P3 stable JSON byte compatibility must be tested in P4a-0 code PR: PENDING
- Five artifact schemas must be validated in P4a-0 code PR: PENDING

## Boundary

This pre-flight record does not implement P4a-0 artifacts. The previously drafted local P4a-0 spike code is intentionally not part of this commit and remains local WIP until the pre-flight commit passes CI.
