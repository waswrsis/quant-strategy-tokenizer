# Changelog

## Token System v2 WP3 PortTemporalSpec + PV-C

- Added `TemporalRule` declarations for v0.4 output ports and deterministic rule resolution.
- Added v0.4 static temporal validation with `validation_v2` diagnostics for unsafe future, unmet temporal requirements, unresolved rules, and temporal conflicts.
- Added PV-C v0.4 strategies, expected diagnostics, expected validation traces, and `expected_artifact_hash_v2()` evidence.
- Kept WP4 numeric policy, WP5 TokenSpec v2 registry, token packs, migration tooling, runtime execution, custom token runtime, and v0.4 CLI authoring out of scope.

## Token System v2 v1.0.3 WP0-WP2 Compliance Retrofit

- Added the remaining v1.0.3 ADRs for Panel layer design, hash stability milestones, and TokenPack propagation/package policy.
- Added `validation_v2` structured diagnostics and deterministic validator registry.
- Added `profile_v2` default profile policy shells for research, paper, pretrade, and production-guarded profiles.
- Extended hash v2 with runtime environment and expected artifact hash kinds.
- Added explicit schema-version shell fields for v0.4 IR, TypeSpec, PortSpec, PortTemporal, and ProfilePolicy material.
- Added Panel TypeSpec shell fields, `StrategyIRV04.capabilities`, canonical `NodeV04.token_ref`, and token-ref-aware signature hashing.
- Kept WP3 temporal resolution, TokenSpec v2 registry, token packs, migration tooling, Panel behavior, custom runtime, and v0.4 CLI authoring out of scope.

## Token System v2 WP2 Structured TypeSpec + PortSpec

- Added structured v2 type models for `TypeSpec`, `ValueType`, and `IntrinsicTemporalSpec`.
- Added v2 port contract models for input requirements, output temporal promises, and node `PortSignature`.
- Added `NodeV04.signature` and canonical shorthand expansion for structured port signatures.
- Added structured signature hash support through `signature_hash_for_ports_v2()`.
- Kept WP3 temporal rule resolution, TokenSpec v2 registry, migration tooling, runtime execution, and v0.4 CLI authoring out of scope.

## Token System v2 WP1 qst-ir/0.4 Shell + Hash Framework

- Added the independent `qst-ir/0.4` shell and `qst-canonical/0.4` canonical byte surface.
- Added the hash v2 framework for graph, param, instance, signature, behavior, token spec, token pack, implementation ref, and audit chain hashes.
- Added read-only legacy loaders for `qst-ir/0.3`, `qst-ir/0.3.1`, and P3 `qst.lock`.
- Added minimal JSON schemas for `qst_ir_0_4` and `qst_lock_0_4`.
- Kept current CLI behavior, legacy strategy hashes, TokenSpec v2, migration tooling, and custom token runtime out of scope.

## Token System v2 WP0 ADR Gate

- Added ADRs for the `qst-ir/0.4` transition, custom token runtime trust model, and Token System v2 P-Validate cases.
- Added the Token System v2 roadmap covering WP0-WP10, embedded P-Validate gates, and P4b-v2 as a deferred standalone stage.
- Marked P4b-old ports, signal extraction, mock adapters, and CLI as accepted legacy infrastructure superseded for future expansion by Token System v2.
- Did not add `qst-ir/0.4`, TokenSpec v2, hash v2, migration tooling, or custom token runtime code.

## P4-core Acceptance

- Recorded P4-core acceptance and final code audit for the accepted P4a/P4b stages.
- Defined P4-core as the artifact, frame, qstpkg artifact, port, signal extraction, mock adapter, and P4b CLI layer.
- Confirmed P0/P1/P2/P3 hash preservation, vocabulary preservation, local final gate, and mock adapter CLI evidence.
- Kept P4c real adapter repositories, P4d semantic detokenize, production integrations, MCP, and numerical equivalence proof out of scope.

## P4b-1 Mock Adapters + CLI

- Added built-in mock adapters for CSV market data, Parquet market data, backtests, execution, and experiment tracking.
- Added P4b CLI commands for adapter discovery, market loading, mock backtesting, mock execution submit/poll, and mock experiment tracking.
- Kept `qst execute`, canonical strategy hashes, lock/package versions, real external adapters, and semantic detokenize out of scope.

## P4b-0 Port Protocols + SignalExtractionPolicy

- Added Universal Port protocols for market data, features, backtests, execution, experiments, package storage, and future RL adapters.
- Added deterministic `execute_to_signals()` support for Decision, Plan, bool TimeSeries, and score TimeSeries outputs.
- Added local entry-point adapter discovery foundation without remote or network lookup.
- Kept mock adapters, adapter CLI commands, `qst execute` behavior changes, and concrete external integrations out of scope.

## P4a-2 qstpkg Artifacts Extension

- Added optional artifact references to `.qstpkg` manifests while preserving legacy P3 package verification.
- Added package helpers and `qst pkg` commands for adding and verifying P4 artifact JSON files.
- Extended package verification to check artifact paths, package file hashes, raw payload references, and backtest artifact refs.
- Kept P3 `qst.lock`, strategy hashes, runtime execution, mutation, search, fork, CSE, and kernel behavior unchanged.

## P4a-1c Multi-Symbol Strict Alignment

- Added strict multi-symbol timestamp grid validation for `MarketFrame` OHLCV bars.
- Preserved existing `compute_frame_hash()` material and P4a-1b frame hash evidence.
- Added JSON, CSV, pandas, Arrow, and Parquet regression coverage for aligned and missing market grids.
- Kept sparse market data, `allow_missing`, nullable DecimalString fields, frequency inference, and runtime changes out of scope.

## P4a-0 Artifact Schema Hard Gate

- Added public canonical JSON bytes support while preserving P3 lock byte compatibility.
- Added P4 artifact base models and schemas for execution reports, backtest evidence, portfolio snapshots, and adapter manifests.
- Added strict DecimalString validation and canonical normalization for artifact numeric fields.
- Added artifact identity rules, POSIX relative path checks, raw payload hash pairing, and adapter version policy checks.
- Added P4a-0 artifact schema, canonical JSON, toy e2e, and P2/P3 backward compatibility tests.
