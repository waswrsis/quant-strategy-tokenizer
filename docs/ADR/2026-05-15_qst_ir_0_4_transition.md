# ADR: qst-ir/0.4 Transition Strategy

Date: 2026-05-15

Status: Accepted

## Context

QST currently has an accepted P0-P4 core based on `qst-ir/0.3` and the additive `qst-ir/0.3.1` fork-lineage extension. That model is sufficient for the accepted TimeSeries-oriented token system, but Token System v2 needs structured types, port-level temporal contracts, explicit state, panel semantics, custom token packs, and stronger token behavior hashes.

Maintaining two active IRs would make token authoring, validation, package verification, migration, and agent behavior ambiguous. Token System v2 therefore uses a single active IR transition.

## Decision

`qst-ir/0.4` is the only active authoring target for Token System v2.

`qst-ir/0.3` and `qst-ir/0.3.1` become legacy IR versions. Legacy IR is still supported for:

- loading existing strategies
- verifying existing `qst.lock` and `.qstpkg` artifacts
- explaining existing strategies
- migrating into `qst-ir/0.4`

Legacy IR is not supported for:

- new strategy authoring
- new token targets
- new recipe targets
- new adapter targets
- direct mutation output
- direct fork output

`qst fork` and future mutation tools must not keep producing `qst-ir/0.3.1` once the v2 migration tooling is active. They must either reject legacy input with a migration instruction or produce `qst-ir/0.4` through the approved migration path.

## Migration Lineage

Migration from legacy IR creates a new identity, not a continuation of the old instance hash.

Migrated `qst-ir/0.4` strategies record lineage with:

```yaml
derived_from:
  kind: ir_migration
  source_ir_version: qst-ir/0.3.1
  source_instance_hash: sha256:...
  migration_tool_version: qst-migrate/0.4.0
```

The legacy source instance hash is historical evidence only. It is not compared directly with the new `qst-ir/0.4` instance hash.

## Hash Boundary

The frozen P0/P1/P2/P3/P4 hashes do not drift.

`qst-ir/0.4` receives its own canonical and hash framework:

- `qst-canonical/0.4`
- graph hash
- param hash
- instance hash
- signature hash
- behavior hash
- token spec hash
- token pack hash
- implementation ref hash
- audit chain hash

No `qst-ir/0.4` hash is defined as equal to a legacy hash. Equality across the migration boundary is not a supported concept.

## Legacy Verification

Existing legacy packages and locks remain verifiable through a legacy loader. Missing v2-only fields such as signature hash, behavior hash, token spec hash, token pack hash, implementation ref hash, and audit chain hash must not make old locks fail by schema shape alone.

## Consequences

- Token System v2 can simplify new feature work around one active IR.
- Legacy compatibility remains explicit but bounded.
- New P4b-v2 adapter design must target `qst-ir/0.4`, not the accepted P4b-old TimeSeries boundary.
- Migration tooling becomes a required gate before legacy strategies can participate in v2 authoring, mutation, fork, or adapter workflows.
