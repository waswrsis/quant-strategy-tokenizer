# ADR: QST P4 Core Construction Boundary

Date: 2026-05-14
Status: Accepted for P4a-0 pre-flight

## Context

P0 through P3 are accepted. P4 begins the universal artifact, frame, port, and adapter layer. The P4 construction manual v1.0.2 is the active construction basis, with the following clarifications locked before code construction begins:

- P4a-0 must start with an ADR and pre-flight before artifact code.
- P4a-0 validates five JSON schemas, not three.
- `DecimalString` must reject `"-0"` even though the v1.0.2 regex would otherwise allow it.
- `stable_json_bytes()` must be byte-compatible with existing P3 canonical lock bytes.
- The mypy command remains the current accepted CI baseline unless a separate hardening PR changes it.

## Decision

P4-core is the universal interchange layer:

- artifact schemas and artifact identities;
- frame models and deterministic frame hashes;
- port protocols;
- mock adapters;
- additive qstpkg artifact sections.

P4-core is not a business adapter implementation layer. `qst-core` must not import vectorbt, qlib, ccxt, mlflow, backtrader, or other business-level third-party adapter frameworks. Real adapters live in separate `qst-adapter-*` repositories.

P4a-0 is a hard gate. It may add:

- `stable_json_bytes()` as the public canonical JSON API;
- `QSTArtifact`, `ProvenanceChain`, and artifact identity calculation;
- `ExecutionReport`, `BacktestEvidence`, `PortfolioSnapshot`, and `AdapterManifest`;
- strict canonical `DecimalString`;
- draft 2020-12 schemas for artifact base, execution report, backtest evidence, portfolio snapshot, and adapter manifest;
- a minimal test-level toy artifact chain.

P4a-0 must not add:

- frames;
- qstpkg artifact sections;
- ports;
- adapters;
- semantic detokenize;
- any change to `qst execute`;
- any change to P0/P1/P2/P3 hashes, lock bytes, package verification, search, fork, mutation, CSE, or kernel behavior.

## Locked Rules

### JSON Schemas

P4a-0 gate item 1 means five schemas must pass draft 2020-12 validation:

- `artifact_base.schema.json`
- `execution_report.schema.json`
- `backtest_evidence.schema.json`
- `portfolio_snapshot.schema.json`
- `adapter_manifest.schema.json`

### DecimalString

P4 uses strict canonical decimal strings:

- valid: `"0"`, `"0.25"`, `"1"`, `"-1.5"`
- invalid: `"-0"`, `"1.0"`, `"1.00"`, `"0.10"`, `"0.50"`, `"1e-3"`, `"+1.0"`, `"001.0"`

`normalize_to_canonical("-0")` and `normalize_to_canonical(Decimal("-0.000"))` must return `"0"`.

### stable_json_bytes

`quant_strategy_tokenizer.canonical_json.stable_json_bytes()` is a public API, but its byte output is defined by compatibility with current P3 canonical lock bytes. It must not introduce an independent line-ending, whitespace, or formatting policy.

### Ports and Adapters

Backtest adapters consume `SignalFrame`, not `StrategyIR`. `execute_to_signals()` is qst-core responsibility and is validated later in P4b-0 by output type:

- Decision
- Plan
- bool `TimeSeries`
- score `TimeSeries` plus threshold

Pure indicator outputs remain unsupported for signal extraction unless a threshold policy makes them signals.

### CLI Boundary

Future submit-plan / poll-execution behavior is separate from existing `qst execute`. P4a-0 must not change `qst execute`.

## Consequences

- P4a-0 code construction may start only after the pre-flight record is complete.
- Any DecimalString fixture migration that touches accepted hash material requires a separate ADR before baseline changes.
- If `stable_json_bytes()` byte compatibility with P3 fails, P4a-0 fails and does not proceed.
- If P0/P1/P2/P3 regression fails, P4a-0 fails and does not proceed.
