# Token System v2 Final Acceptance

Date: 2026-05-15

Acceptance standard: `acceptance-plan/0.1.1`

## Status

Token System v2 is accepted through WP10 at the code freeze baseline `1ede6998bf442c22102b6a83530ef89a0cdadaaa`.

Active target:

- `qst-ir/0.4`
- `qst-canonical/0.4`

Legacy support:

- `qst-ir/0.3` and `qst-ir/0.3.1` remain loadable, verifiable, explainable, and migratable.
- Legacy IR is not an active target for new token, recipe, adapter, mutation, fork, Panel, custom-token, or migration output.

## Accepted Work Packages

| WP | Accepted capability |
|---|---|
| WP0 | Six ADR gate under v1.0.3. |
| WP1 | `qst-ir/0.4` shell, canonical bytes, hash v2, validation/profile shells, legacy loaders. |
| WP2 | Structured TypeSpec, PortSpec, `TokenRefV04`, signatures, capability shell. |
| WP3 | TemporalRule, static temporal validation, PV-C. |
| WP4 | NumericPolicy, TokenEvolutionPolicy, lifecycle and behavior hash material. |
| WP5 | TokenSpecV2, TokenPackManifestV2, TokenRegistryV2, token/pack hashes. |
| WP5b | qst-lock/0.4 token entries and qstpkg TokenPack propagation without execution. |
| WP6a | Basic state reference helpers and state-basic TokenPack. |
| WP6b | Closed-set FSM reference helper and state-fsm TokenPack. |
| WP6c | PV-A state-heavy reference artifacts. |
| WP7 | Decision Algebra, true monoids, fold policies, aggregators, legacy reduce classifier. |
| WP8a | Panel detail design gate and draft schemas. |
| WP8b | Panel type-layer validation and `panel_type` capability. |
| WP8c | Panel operator reference semantics and `panel_ops` TokenPack. |
| WP8d | WeightPanel operators and `panel_weights` TokenPack. |
| WP8e | PV-B Panel reference strategies; `panel_recipes` remains deferred. |
| WP9 | Custom-token verify/approve/execute boundary and PV-D. |
| WP10 | Legacy strategy and qstpkg migration tooling to v0.4 snapshots. |

## ADR-To-Test Mapping

| ADR | Key constraint | Verification path |
|---|---|---|
| `2026-05-15_qst_ir_0_4_transition.md` | v0.4 is the active authoring target; legacy versions are migration sources. | `tests/ir_v04`, `tests/migration_v2`, `tests/e2e/*compat*` |
| `2026-05-15_qst_custom_token_runtime_trust_model.md` | `verify_integrity` never imports or executes custom code; approval is local trust; execution requires a grant. | `tests/custom_runtime_v2`, `tests/cli/test_cli_wp9_token.py`, `docs/ACCEPTANCE/SECURITY_BOUNDARY_REPORT.md` |
| `2026-05-15_qst_token_system_v2_p_validate_cases.md` | PV-A/PV-B/PV-C/PV-D have fixtures, traces, diagnostics, and expected hashes. | `tests/e2e/test_p_validate_*.py` |
| `2026-05-15_qst_panel_layer_detail_design.md` | Panel type, ops, and weights are capability-gated; recipes remain disabled. | `tests/panel_v2`, `tests/e2e/test_p_validate_panel_v04.py` |
| `2026-05-15_qst_hash_stability_milestones.md` | Accepted hash/schema semantics cannot drift silently. | `tests/hash_v2`, `tests/e2e/test_03_hash_not_drift.py`, `docs/ACCEPTANCE/HASH_STABILITY_REPORT.md` |
| `2026-05-15_qst_tokenpack_propagation_package_policy.md` | TokenPack propagation is metadata-only; qstpkg verification does not execute embedded source. | `tests/tokens_v2`, `tests/custom_runtime_v2/test_package_integration.py` |
| `2026-05-15_qst_panel_capability_schema_correction.md` | Granular Panel capabilities replace the old umbrella `panel`. | `tests/panel_v2/test_wp8b_panel_type_layer.py`, `tests/ir_v04/test_capabilities_and_token_ref.py` |

## P-Validate Summary

| Gate | Purpose | Status | Representative trace hash | Representative diagnostics hash |
|---|---|---|---|---|
| PV-A | State/FSM | PASS | `sha256:f9e3ba85328b9f5c7eafa7ca40426bc6e5ee029c1147680cd2a027f3b537425e` | `sha256:acbafdd359c12b518959334828fac50cf7dfcbf14b6e3143c68fdff718f5ae24` |
| PV-B | Panel/Weight | PASS | `sha256:13231b975370d110149a6c996b2d88e31c34967ce2c93a0fcc33f0e73087c95a` | `sha256:bb89f8fa67fe9f3f75a9001edb5275f1906f2a8b476cb8e475d9b4bf87ec1edf` |
| PV-C | Temporal | PASS | `sha256:de782e9fe73579e0383b3c61b3f0ca0437cdf1a39cbd33612f246bdcf4c0bd15` | `sha256:5ef9f26f8898f8c3f75199c1c2d8b600935326847bf0ee4d13d452a83a1dbc7a` |
| PV-D | Custom Token | PASS | `sha256:0d305ba51aa410fb7a851a6d11cf70883c11f32a5a119c5d62ebb2049951ee33` | `sha256:b8a126ed5692f5c1994b0e63ed3d46cb560cc5e978f0042cf5c331614a85344a` |

## Accepted Boundaries

- v0.4 runtime execution is not broadly implemented.
- v0.4 authoring CLI is not complete.
- Custom-token runtime v0.1 has no sandbox.
- qstpkg contents are not portable approval.
- Panel recipes remain disabled.
- Panel / Weight reference numerics are semantic, not bit-exact.
- Migration creates new v0.4 identity and does not claim semantic equivalence.

## Result

Token System v2 is accepted as a typed, auditable, temporal-safe, state-aware, panel-capable, custom-token-extensible token kernel foundation. Future changes to accepted v0.4 semantics require a new ADR or explicit work package.
