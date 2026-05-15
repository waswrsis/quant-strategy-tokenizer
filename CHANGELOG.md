# Changelog

## Token System v2 Security + Semantic Cleanup

- Hardened WP9 custom-token approval so executable approvals require both `allow_token=true` and `ack_risk=true`, and persisted incomplete approvals are ignored defensively.
- Enforced `ExecutionGrant` expiry and run-id binding, and rejected undeclared extra custom-token output ports.
- Strengthened `installed_distribution` implementation hashing to use RECORD hashes or installed file bytes, with stable incomplete-RECORD diagnostics.
- Removed the deprecated umbrella `panel` capability from `qst-ir/0.4`, deferred `propagate_missing`, and rejected unsupported `side="both"` long/short weight conversion.
- Tightened v0.4 temporal semantics for `event_time` and signed `param_max_floor`, and made TokenSpec risk metadata structured through `TokenRiskSpec`.

## Token System v2 WP10 Migration Tooling

- Added `qst migrate-ir` and `qst migrate-package` for legacy `qst-ir/0.3` / `0.3.1` to `qst-ir/0.4` migration snapshots.
- Added migration lineage with source instance hash, target core registry hash, and `qst-migrate/0.4.0`.
- Added v0.4 package verification for migrated `qst-lock/0.4` snapshots while preserving legacy qstpkg verification.
- Kept broad v0.4 runtime execution, semantic equivalence, numerical equivalence, P4b-v2 adapters, and legacy hash changes out of scope.

## Token System v2 WP9 Custom Token Runtime + PV-D

- Added custom token integrity, authorization, approval, execution grant, and audit models for `qst-ir/0.4`.
- Added a core service that keeps `verify_integrity` free of imports/execution and requires local approval plus a hash-bound `ExecutionGrant` before `python_entrypoint` execution.
- Added qstpkg TokenPack verification integration that checks embedded pack metadata/source hashes without executing embedded source.
- Added the deterministic PV-D `my_pack.kalman_ema` TokenPack, fixtures, expected diagnostics, and trace artifacts.
- Added `qst token verify`, `qst token approve`, approval listing/revocation, and `qst token execute` as explicit separate operations.
- Kept sandboxing, WP10 migration, broad v0.4 strategy runtime, portable qstpkg trust, and legacy `qst execute` changes out of scope.

## Token System v2 WP8e PV-B Panel Reference Strategies

- Added PV-B v0.4 Panel reference strategies for top/bottom market-neutral selection and BTC residual mean reversion.
- Added deterministic Panel fixtures plus expected diagnostics and trace artifacts with `expected_artifact_hash_v2()` evidence.
- Added a minimal PV-B runner that validates `qst-ir/0.4` before composing accepted WP8b/WP8c/WP8d reference helpers.
- Fixed WeightPanel canonical row sorting so `weight_kind` and `normalized` survive model construction.
- Kept `panel_recipes`, recipe TokenSpecs/TokenPacks, legacy recipe registry entries, runtime execution, migration tooling, adapters, WP9, WP10, and v0.4 CLI authoring out of scope.

## Token System v2 WP8d Weight Operators

- Added deterministic WeightPanel reference helpers for `weight.normalize_gross`, `weight.cap_per_symbol`, and `weight.market_neutral`.
- Accepted `panel_weights` only when `panel_type` is also explicitly declared; `panel_ops` is not required for validated raw `WeightPanel` inputs.
- Added validation that weight operators consume typed `WeightPanel` outputs with output-scoped `metadata.panel_type_by_output`, not arbitrary `Panel[decimal]`.
- Added `qst-tokenpack-panel-weights/0.1.0` with core TokenSpecV2 metadata for WP8d weight operators.
- Canonicalized DecimalString operator params before semantics and hash material, including equivalent `target_gross` and cap values.
- Kept simultaneous gross/cap optimization, order generation, execution artifacts, risk controls, Panel recipes, runtime execution, migration tooling, adapters, and v0.4 CLI authoring out of scope.

## Token System v2 WP8c Panel Operators

- Added deterministic Panel operator reference helpers for mask, rank, zscore, top/bottom-k, demean, group-demean, winsorize, single-factor residualize, and selection-to-raw-weight conversion.
- Accepted `panel_ops` only when `panel_type` is also explicitly declared; kept the umbrella `panel`, `panel_weights`, `panel_recipes`, `custom_token_runtime`, and `weight.*` operators rejected.
- Added `qst-tokenpack-panel-ops/0.1.0` with core TokenSpecV2 metadata for WP8c Panel and selection operators.
- Fixed WP8c numeric semantics for finite-only values, canonical symbol order, stable tie behavior, zscore zero-variance handling, nearest-rank winsorization, and raw WeightPanel output.
- Kept Panel recipes, weight normalization, market-neutral constraints, runtime execution, migration tooling, adapters, and v0.4 CLI authoring out of scope.

## Token System v2 WP8b Panel Type Layer

- Added a schema correction ADR for granular Panel capabilities and accepted `panel_type` while keeping `panel`, `panel_ops`, `panel_weights`, and `panel_recipes` rejected.
- Added `panel_v2` type-layer models for PanelRepresentation, UniverseMask, MissingPolicy, GroupSpec, SelectionPanelType, WeightPanelType, and output-scoped PanelTypeLayerSpec.
- Added v0.4 validation for `metadata.panel_type_by_output`, Panel output capability requirements, Panel operator gates, and Panel state auto-broadcast rejection.
- Added `signature_hash_for_panel_ports_v2()` so Panel type-layer metadata is semantic hash material while non-panel signature hashes remain stable.
- Kept TypeSpec shape/defaults/schema, Panel operators, Weight operators, Panel recipes, TokenSpecs, TokenPacks, runtime execution, migration tooling, and v0.4 CLI authoring out of scope.

## Token System v2 WP8a Panel Detail Design Gate

- Added `docs/PANEL_LAYER_DESIGN_V04.md` to freeze sparse logical Panel representation, UniverseMask, MissingPolicy, GroupSpec, SelectionPanel / WeightPanel boundaries, single-factor residualize, Panel temporal joins, and Panel / State constraints.
- Added WP8a draft JSON Schemas for Panel representation, universe masks, missing policy, group specs, selection/weight panels, and temporal/state boundaries.
- Added schema hash evidence and design-gate tests proving the WP2 Panel TypeSpec shell field set is unchanged and the `panel` capability remains rejected.
- Corrected the Token System v2 roadmap naming so WP8a is the Panel Detail Design Gate and WP8b begins the Panel Type Layer.
- Kept Panel operators, Panel TokenSpecs, TokenPacks, runtime execution, migration tooling, custom token runtime, and v0.4 CLI authoring out of scope.

## Token System v2 WP7 Decision Algebra

- Added v0.4 `decision_v2` models for `DecisionV2`, true monoids, fold policies, aggregators, and structured combine results.
- Added deterministic reference helpers for `combine_decisions`, `fold_decisions`, and `aggregate_decisions`.
- Added legacy `decision.reduce` migration classification without silently mapping legacy errors into decisions.
- Added `qst-tokenpack-decision-algebra/0.1.0` with core TokenSpecV2 metadata for seven Decision Algebra tokens.
- Added Decision Algebra JSON schemas and test coverage for monoid laws, fold-policy truth tables, aggregators, token hashes, and legacy migration diagnostics.
- Kept legacy runtime execution, legacy token registration, strategy mutation, Panel behavior, custom token runtime, migration tooling, and v0.4 CLI authoring out of scope.

## Token System v2 WP6c State Recipes + PV-A

- Added PV-A state-heavy v0.4 reference strategies for cooldown, market freeze, circuit breaker, observe period, and minimal slot budget cases.
- Added deterministic state fixtures plus expected diagnostics and trace artifacts with expected artifact hashes.
- Added a minimal PV-A runner that uses WP6a/WP6b reference helpers and emits deterministic trace artifacts.
- Added PV-A e2e coverage for artifact matching, hash verification, case outcomes, and FSM replay checks.
- Kept legacy recipes, v0.4 runtime execution, Decision Algebra, Panel behavior, custom token runtime, migration tooling, and v0.4 CLI authoring out of scope.

## Token System v2 WP6b State FSM

- Added `state_v2.FSMDefinition` and `FSMTransition` with closed state/event set validation.
- Added deterministic `state_fsm()` reference semantics with reset-before-event handling, failure policies, structured diagnostics, and transition traces.
- Added `replay_fsm_trace()` for deterministic FSM trace replay checks.
- Added `qst-tokenpack-state-fsm/0.1.0` with core TokenSpecV2 metadata for `core.state.fsm` and a dependency on `qst-tokenpack-state-basic >=0.1.0`.
- Added `qst_state_fsm_0_4` JSON schema.
- Kept state recipes, PV-A, legacy runtime execution, migration tooling, Panel behavior, custom token runtime, and v0.4 CLI authoring out of scope.

## Token System v2 WP6a State Basic

- Added `state_v2.StatePolicy` with deterministic warmup, reset, and missing-event policy defaults.
- Added state transition trace models and deterministic reference helpers for `state.delay`, `state.accumulate`, and `state.edge_detect`.
- Added `ReducerRegistry` with registered-only reducers and built-ins `sum`, `count`, `last`, `min`, and `max`.
- Added `qst-tokenpack-state-basic/0.1.0` with core TokenSpecV2 metadata for `core.state.delay`, `core.state.accumulate`, and `core.state.edge_detect`.
- Added `qst_state_policy_0_4` JSON schema.
- Kept FSM, state recipes, PV-A, legacy runtime execution, migration tooling, Panel behavior, custom token runtime, and v0.4 CLI authoring out of scope.

## Token System v2 WP5b Lock + Package Integration

- Added v0.4 TokenSpec / TokenPack lock snapshot models for token hashes, pack hashes, implementation-reference hashes, runtime-environment hashes, origin, attestation, and risk metadata.
- Added deterministic metadata-only verification diagnostics for missing TokenPacks, TokenPack hash mismatch, TokenSpec hash mismatch, implementation-ref hash mismatch, and runtime-environment hash mismatch.
- Added additive qstpkg `token_packs` manifest metadata with `none`, `spec_only`, and `spec_and_source` embedding policies.
- Extended `qst_lock_0_4` and `qst_package_manifest` JSON schemas with TokenPack propagation fields while keeping legacy qstpkg manifests valid.
- Kept custom token execution, source-tree packaging layout, migration tooling, runtime integration, Panel behavior, and v0.4 CLI authoring out of scope.

## Token System v2 WP5 TokenSpec v2 + Registry + TokenPack

- Added `tokens_v2.TokenSpecV2` with canonical token refs, v2 port signatures, numeric policy, lifecycle, origin, attestation, and canonical metadata refs.
- Added `TokenPackManifestV2` and TokenPack dependency declarations with PEP 440 validation.
- Added deterministic TokenPack dependency validation for transitive resolution, missing packs, version mismatch, hash mismatch, and cycles.
- Added `TokenRegistryV2` with core namespace protection, duplicate handling, project-local override diagnostics, stable resolution logs, and non-self-trusted attestation diagnostics.
- Added typed TokenSpec and TokenPack hash helpers plus JSON schemas.
- Kept WP5b lock/qstpkg propagation, custom token execution, runtime integration, migration tooling, Panel behavior, and v0.4 CLI authoring out of scope.

## Token System v2 WP4 NumericPolicy + TokenEvolutionPolicy

- Added `numeric_v2.NumericPolicy` with explicit representation, determinism, reduction, `NaN`, and infinity policy fields.
- Added `token_evolution_v2.TokenEvolutionPolicy` and lifecycle status material.
- Added WP4 behavior hash material requiring `numeric_policy` and including lifecycle status.
- Extended `profile_v2` with numeric-policy risk decisions.
- Added NumericPolicy / TokenEvolutionPolicy JSON schemas and `docs/TOKEN_EVOLUTION_POLICY.md`.
- Kept WP5 TokenSpec v2 registry, token packs, migration tooling, runtime execution, custom token runtime, Panel behavior, and v0.4 CLI authoring out of scope.

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
