# Token System v2 Roadmap

Date: 2026-05-15

Status: WP0-WP8b accepted under the v1.0.3 standard. WP8b adds the Panel Type Layer and `panel_type` capability validation.

## Direction

Token System v2 moves QST from the accepted TimeSeries-oriented token system to a typed, auditable, temporal-safe, state-aware, panel-capable token kernel.

The target active versions are:

- `qst-ir/0.4`
- `qst-canonical/0.4`

Legacy versions remain loadable and verifiable, but new authoring moves to `qst-ir/0.4`.

## Work Package Order

| WP | Name | Status |
|---|---|---|
| WP0 | ADR Gate | accepted |
| WP1 | qst-ir/0.4 shell + canonical/hash framework | accepted |
| WP2 | Structured TypeSpec + PortSpec | accepted |
| WP3 | PortTemporalSpec + PV-C | accepted |
| WP4 | NumericPolicy + TokenEvolutionPolicy | accepted |
| WP5 | TokenSpec v2 + Registry + TokenPack | accepted |
| WP5b | Lock + Package Integration | accepted |
| WP6a | State Basic | accepted |
| WP6b | State FSM | accepted |
| WP6c | State Recipes + PV-A | accepted |
| WP7 | Decision Algebra | accepted |
| WP8a | Panel Detail Design Gate | accepted |
| WP8b | Panel Type Layer | accepted |
| WP8c | Panel Operators | not started |
| WP8d | Weight Operators | not started |
| WP8e | Panel Recipes + PV-B | not started |
| WP9 | Custom Token Runtime + PV-D | not started |
| WP10 | Migration Tooling | not started |
| Final | Token System v2 acceptance | not started |

## WP0 Decisions

WP0 accepted six ADRs under the v1.0.3 construction standard:

- `docs/ADR/2026-05-15_qst_ir_0_4_transition.md`
- `docs/ADR/2026-05-15_qst_custom_token_runtime_trust_model.md`
- `docs/ADR/2026-05-15_qst_token_system_v2_p_validate_cases.md`
- `docs/ADR/2026-05-15_qst_panel_layer_detail_design.md`
- `docs/ADR/2026-05-15_qst_hash_stability_milestones.md`
- `docs/ADR/2026-05-15_qst_tokenpack_propagation_package_policy.md`

Locked decisions:

- `qst-ir/0.4` is the only active Token System v2 authoring target.
- `qst-ir/0.3` and `qst-ir/0.3.1` are legacy: load, verify, explain, migrate.
- Legacy IR is not a target for new token, recipe, adapter, mutation, or fork output once v2 migration is active.
- Custom token runtime v0.1 has no sandbox.
- P-Validate gates are embedded in their owning work packages.
- Panel declarations are parsed before panel behavior is accepted.
- Hash stability is staged by hash kind and work package.
- TokenPack propagation policy is additive and never executes embedded source during verification.

## WP1 Accepted Scope

WP1 adds the minimal Token System v2 kernel shell without changing accepted legacy behavior:

- `quant_strategy_tokenizer.ir_v04` with `StrategyIRV04`, fixed `qst-ir/0.4`, and fixed `qst-canonical/0.4`.
- Independent `canonicalize_v04()` and `canonical_bytes_v04()` using public canonical JSON bytes.
- `quant_strategy_tokenizer.hash_v2` with graph, param, instance, signature, behavior, token spec, token pack, implementation ref, runtime environment, expected artifact, and audit chain hash functions.
- `quant_strategy_tokenizer.validation_v2` with structured diagnostics, result semantics, and deterministic validator registry.
- `quant_strategy_tokenizer.profile_v2` with accepted default profile policy shells for `research`, `paper`, `pretrade`, and `production_guarded`.
- Read-only legacy loaders for `qst-ir/0.3`, `qst-ir/0.3.1`, and P3 `qst.lock`.
- Minimal JSON schemas for `qst_ir_0_4`, `qst_lock_0_4`, TypeSpec, PortSpec, and ProfilePolicy shell material.

WP1 does not add TokenSpec v2, token pack loading, custom token runtime, migration tooling, or v0.4 CLI authoring.

## WP2 Accepted Scope

WP2 adds the structured type and port contract layer used by future TokenSpec v2 work:

- `quant_strategy_tokenizer.types_v2` with `TypeSpec`, `ValueType`, and `IntrinsicTemporalSpec`.
- `quant_strategy_tokenizer.ports_v2` with `InputSpec`, `OutputSpec`, `PortSignature`, `TemporalRequirement`, and `PortTemporalSpec`.
- Explicit `schema_version` fields for IR, TypeSpec, PortSpec, PortTemporal, and ProfilePolicy shells.
- Panel TypeSpec shell fields for Stage 2B shape stability; panel behavior remains disabled.
- `NodeV04.signature` as the canonical place for v0.4 node port contracts; graph wiring remains in `NodeV04.inputs`.
- `NodeV04.token_ref` with canonical `namespace`, `name`, `version`, and `behavior_version` fields while retaining WP1 compatibility fields.
- `StrategyIRV04.capabilities` defaulting to `["core"]`; `panel` and `custom_token_runtime` capabilities produce v2 validation errors in WP2.
- `signature_hash_for_ports_v2()` for structured TypeSpec / PortSpec hash material, with optional token-ref material.
- `qst_ir_0_4` schema support for structured node signatures.

WP2 does not add WP3 temporal rule resolution, TokenSpec v2 registry, token packs, migration tooling, runtime execution, Panel behavior, custom token runtime, or v0.4 CLI authoring.

## WP3 Accepted Scope

WP3 adds static temporal safety validation for `qst-ir/0.4` shell documents:

- `TemporalRule` declarations on `OutputSpec`.
- Rule resolution for constant values, input inheritance, param-derived min history, input joins, predicate branches, trailing-window history, and centered-window unsafe future declarations.
- `validate_temporal_v04()` and `trace_temporal_validation_v04()` using `validation_v2` diagnostics.
- PV-C strategies, expected diagnostics, expected validation traces, and `expected_artifact_hash_v2()` evidence.

WP3 does not add WP4 numeric policy, WP5 TokenSpec v2 registry, token packs, migration tooling, runtime execution, custom token runtime, or v0.4 CLI authoring.

## WP4 Accepted Scope

WP4 adds behavior-policy material required before TokenSpec v2 registry work:

- `quant_strategy_tokenizer.numeric_v2.NumericPolicy` with explicit representation, determinism level, reduction order, `NaN` policy, and infinity policy.
- Numeric policy risk classification where unknown or platform-dependent numeric behavior is high risk.
- `quant_strategy_tokenizer.token_evolution_v2.TokenEvolutionPolicy` and `TokenLifecycleStatus`.
- WP4 behavior material helper requiring `numeric_policy` and including lifecycle status in `behavior_hash_v2()` material.
- Profile policy decisions for numeric-policy risk and lifecycle states.
- JSON schemas for NumericPolicy and TokenEvolutionPolicy.
- `docs/TOKEN_EVOLUTION_POLICY.md` as the accepted evolution policy record.

WP4 does not add WP5 TokenSpec v2 registry, token packs, registry resolution, recipe migration, runtime execution, custom token runtime, Panel behavior, or v0.4 CLI authoring.

## WP5 Accepted Scope

WP5 adds portable v0.4 token metadata and deterministic registry validation:

- `quant_strategy_tokenizer.tokens_v2.TokenSpecV2` with canonical `TokenRefV04`, `NumericPolicy`, lifecycle, port signatures, metadata refs, risk/tests/dependencies, origin, and attestation claims.
- `TokenPackManifestV2` with PEP 440 versioning, declared namespaces, embedded-source flags, TokenSpec contents, and TokenPack dependencies.
- Deterministic TokenPack dependency validation for transitive dependencies, missing packs, version mismatches, hash mismatches, and cycles.
- `TokenRegistryV2` built only from TokenPack manifests, with core namespace protection, duplicate handling, project-local override rules, stable resolution logs, and non-self-trusted attestation diagnostics.
- Typed hash helpers for TokenSpec and TokenPack material.
- JSON schemas for TokenSpec v2 and TokenPack v2.

WP5 does not add WP5b lock/qstpkg propagation, custom token execution, runtime integration, migration tooling, Panel behavior, or v0.4 CLI authoring.

## WP5b Accepted Scope

WP5b makes TokenSpec / TokenPack metadata portable through future v0.4 locks and existing qstpkg manifests without executing custom token code:

- `TokenLockEntryV04` records canonical `TokenRefV04`, TokenSpec hash, TokenPack hash, implementation-ref hash, runtime-environment hash, origin tier, attestation kind, and risk level.
- `TokenPackLockDependencyV04` records TokenPack dependency identity for `qst-lock/0.4`.
- Deterministic lock verification reports missing TokenPack, TokenPack hash mismatch, TokenSpec hash mismatch, implementation-ref hash mismatch, and runtime-environment hash mismatch diagnostics.
- `PackageManifest.token_packs` additively records `embedded_policy` and TokenPack references while keeping old qstpkg manifests valid.
- qstpkg TokenPack verification checks referenced pack availability and hash equality without importing or executing embedded source.
- JSON schemas for `qst_lock_0_4` and `qst_package_manifest` include the additive TokenPack propagation fields.

WP5b does not add custom token execution, source-tree packaging layout, WP6 state, migration tooling, runtime integration, Panel behavior, v0.4 CLI authoring, or legacy qst.lock behavior changes.

## WP6a Accepted Scope

WP6a adds basic deterministic state semantics for v0.4 metadata and tests:

- `quant_strategy_tokenizer.state_v2.StatePolicy` with accepted defaults for warmup, reset, and missing-event policy.
- `StateTraceEvent` and `StateExecutionTrace` for deterministic policy and state transition tracing.
- Reference helpers for `state.delay`, `state.accumulate`, and `state.edge_detect`.
- `ReducerRegistry` with registered-only reducers and built-ins `sum`, `count`, `last`, `min`, and `max`.
- `qst-tokenpack-state-basic/0.1.0` with core TokenSpecV2 metadata for `core.state.delay`, `core.state.accumulate`, and `core.state.edge_detect`.
- JSON schema for `qst-state-policy/0.4`.

WP6a does not add FSM behavior, state recipes, PV-A artifacts, legacy runtime execution, migration tooling, Panel behavior, custom token runtime, or v0.4 CLI authoring.

## WP6b Accepted Scope

WP6b adds deterministic closed-set FSM semantics for v0.4 metadata and tests:

- `FSMDefinition` and `FSMTransition` with closed state/event set validation.
- Failure policies `stay`, `transition_to_unknown`, and `raise`; `transition_to_unknown` requires an explicit closed `unknown_state`.
- `state_fsm()` reference semantics with reset-before-event behavior, structured diagnostics, and complete transition traces.
- `replay_fsm_trace()` for deterministic state sequence replay checks.
- `qst-tokenpack-state-fsm/0.1.0` with core TokenSpecV2 metadata for `core.state.fsm`.
- A declared TokenPack dependency from `qst-tokenpack-state-fsm` to `qst-tokenpack-state-basic >=0.1.0`.
- JSON schema for `qst-state-fsm/0.4`.

WP6b does not add state recipes, PV-A artifacts, legacy runtime execution, migration tooling, Panel behavior, custom token runtime, or v0.4 CLI authoring.

## WP6c Accepted Scope

WP6c adds the PV-A state-heavy reference gate:

- Five v0.4 reference strategies: cooldown, market freeze, circuit breaker, observe period, and minimal slot budget.
- Deterministic fixture JSON under `fixtures/v04/p_validate/state`.
- Expected diagnostics and state trace artifacts with `expected_artifact_hash_v2()` evidence.
- A minimal `state_v2` PV-A runner that dispatches to WP6a/WP6b reference helpers and emits deterministic artifacts.
- Replay checks for FSM-backed PV-A cases.

WP6c does not add legacy recipes, v0.4 runtime execution, Decision Algebra, Panel behavior, custom token runtime, migration tooling, or v0.4 CLI authoring.

## WP7 Accepted Scope

WP7 adds v0.4 Decision Algebra metadata and deterministic reference semantics:

- `DecisionKind = accept | reject | unknown | block`; errors are diagnostics, not decisions.
- True monoids for `decision.unknown_propagating_and` and `decision.any_accept`.
- Fold policies for `decision.strict_and` and `decision.permissive_and` as monoid-backed finalizers.
- Aggregators for `decision.majority`, `decision.weighted_vote`, and `decision.quorum`.
- `qst-tokenpack-decision-algebra/0.1.0` with core TokenSpecV2 metadata for the seven decision algebra tokens.
- Legacy `decision.reduce` migration classification with non-migratable error semantics reported as diagnostics.

WP7 does not add legacy runtime execution, legacy token registration, strategy mutation, CLI migration tooling, Panel behavior, custom token runtime, or v0.4 CLI authoring.

## WP8a Accepted Scope

WP8a freezes the Panel layer detail design before any Panel behavior is enabled:

- `docs/PANEL_LAYER_DESIGN_V04.md` records PanelRepresentation, UniverseMask, MissingPolicy, GroupSpec, SelectionPanel / WeightPanel boundaries, single-factor residualize, Panel temporal joins, and Panel / State boundaries.
- Draft JSON Schemas cover `qst-panel-representation/0.4`, `qst-panel-universe-mask/0.4`, `qst-panel-missing-policy/0.4`, `qst-panel-group-spec/0.4`, `qst-panel-selection-weight/0.4`, and `qst-panel-temporal-state/0.4`.
- `sparse_logical` is a Panel representation, not a MissingPolicy.
- `UniverseMask=false` means out of universe, not missing data.
- MissingPolicy applies only when `UniverseMask=true` and a value is absent; the default is `error_on_missing`.
- `dynamic_mapping` GroupSpec is deferred and rejected by the WP8a schema.
- `SelectionPanel` and `WeightPanel` remain distinct wire concepts; weight normalization belongs to WP8d.
- `panel.residualize/v1` is single-factor only: `Panel[float] + TimeSeries[float] -> Panel[float]`.
- Panel temporal joins use the declared input port-temporal join formula.
- `Panel[State]` is shell-only; `state.fsm` does not auto-broadcast per symbol.
- The WP2 `TypeSpec` Panel shell field set is frozen and unchanged.

WP8a does not enable the `panel` capability, modify `TypeSpec`, add Panel TokenSpecs or TokenPacks, add Panel operators, add Panel recipes, add runtime execution, add migration tooling, or add v0.4 CLI authoring.

## WP8b Accepted Scope

WP8b enables Panel type-layer validation without enabling Panel operators:

- `docs/ADR/2026-05-15_qst_panel_capability_schema_correction.md` records the schema correction that adds granular Panel capabilities.
- `panel_type` is accepted by `validate_ir_v04()`.
- The old umbrella `panel` capability remains parseable but is rejected.
- `panel_ops`, `panel_weights`, `panel_recipes`, and `custom_token_runtime` remain rejected.
- `quant_strategy_tokenizer.panel_v2` adds models for PanelRepresentation, UniverseMask, PanelMissingPolicy, GroupSpec, SelectionPanelType, WeightPanelType, and PanelTypeLayerSpec.
- Panel semantic metadata must be output-scoped under `node.metadata.panel_type_by_output`.
- `metadata.panel_type` is rejected as an unsafe non-output-scoped location.
- Panel type-layer metadata enters Panel signature hash material through `signature_hash_for_panel_ports_v2()`.
- `state.fsm` does not auto-broadcast over Panel inputs.
- `qst_typespec_0_4.schema.json`, the TypeSpec field set, TypeSpec enum/defaults, and non-panel signature hashes remain unchanged.

WP8b does not add Panel TokenSpecs, Panel TokenPacks, Panel operators, weight operators, Panel recipes, runtime execution, migration tooling, or v0.4 CLI authoring.

## P-Validate Gates

| Gate | Owning WP | Purpose |
|---|---|---|
| PV-C | WP3 | Temporal safety strategy |
| PV-A | WP6c | State-heavy strategy |
| PV-B | WP8e | Panel / cross-sectional strategy |
| PV-D | WP9 | Custom token strategy |

If a P-Validate gate fails, the owning work package fails.

## Legacy And P4 Boundary

The accepted P0-P4 core remains stable:

- P0/P1/P2/P3/P4 frozen hashes do not drift.
- P4a artifacts, frames, qstpkg, and package artifact extension are retained.
- P4b-old ports, signal extraction, mock adapters, and CLI are accepted legacy infrastructure.
- P4b-old is superseded for future adapter expansion by Token System v2.

P4b-v2 is deferred as a standalone design after Token System v2 acceptance.

Future P4b-v2 design must target:

- `qst-ir/0.4`
- structured TypeSpec and PortSpec
- panel-aware signals, weights, and state
- custom token runtime and token pack verification
- adapter manifest v2

## Global Invariants

- No qst-core import of business adapter frameworks.
- No arbitrary lambda, eval, or YAML-embedded Python.
- Custom tokens require explicit implementation reference and risk policy.
- All TokenSpec v2 records have token spec hashes.
- All token packs have token pack hashes.
- `behavior_version` is never silently changed.
- Accepted legacy packages and locks remain verifiable through the legacy path.
