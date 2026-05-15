# Token System v2 Roadmap

Date: 2026-05-15

Status: WP0 ADR Gate accepted. WP1 has not started.

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
| WP1 | qst-ir/0.4 shell + canonical/hash framework | not started |
| WP2 | Structured TypeSpec + PortSpec | not started |
| WP3 | PortTemporalSpec + PV-C | not started |
| WP4 | NumericPolicy + TokenEvolutionPolicy | not started |
| WP5 | TokenSpec v2 + Registry + TokenPack | not started |
| WP6a | State Basic | not started |
| WP6b | State FSM | not started |
| WP6c | State Recipes + PV-A | not started |
| WP7 | Decision Algebra | not started |
| WP8a | Panel Type Layer | not started |
| WP8b | Panel Operators | not started |
| WP8c | Weight Operators | not started |
| WP8d | Panel Recipes + PV-B | not started |
| WP9 | Custom Token Runtime + PV-D | not started |
| WP10 | Migration Tooling | not started |
| Final | Token System v2 acceptance | not started |

## WP0 Decisions

WP0 accepted three ADRs:

- `docs/ADR/2026-05-15_qst_ir_0_4_transition.md`
- `docs/ADR/2026-05-15_qst_custom_token_runtime_trust_model.md`
- `docs/ADR/2026-05-15_qst_token_system_v2_p_validate_cases.md`

Locked decisions:

- `qst-ir/0.4` is the only active Token System v2 authoring target.
- `qst-ir/0.3` and `qst-ir/0.3.1` are legacy: load, verify, explain, migrate.
- Legacy IR is not a target for new token, recipe, adapter, mutation, or fork output once v2 migration is active.
- Custom token runtime v0.1 has no sandbox.
- P-Validate gates are embedded in their owning work packages.

## P-Validate Gates

| Gate | Owning WP | Purpose |
|---|---|---|
| PV-C | WP3 | Temporal safety strategy |
| PV-A | WP6c | State-heavy strategy |
| PV-B | WP8d | Panel / cross-sectional strategy |
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
