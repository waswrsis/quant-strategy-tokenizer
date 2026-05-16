# ADR: TokenPack Propagation and Package Policy

Date: 2026-05-15

Status: Accepted

## Context

Token System v2 introduces token packs as the unit that binds TokenSpec v2,
implementation references, behavior hashes, and audit-chain material. A strategy
lock or package that references custom or non-core tokens must be reproducible
without relying on mutable registries alone.

At the same time, P0-P4 accepted packages and locks must remain valid. TokenPack
support is additive to `qst-ir/0.4` and must not rewrite legacy `qst.lock` or
`.qstpkg` semantics.

## Decision

`qst-ir/0.4` package policy will support three TokenPack propagation modes:

- `none`: package records token pack identity hashes only.
- `spec_only`: package embeds TokenSpec v2 and pack manifests, but no source.
- `spec_and_source`: package embeds TokenSpec v2, manifests, and source
  references or source snapshots where policy permits.

Verification may read embedded TokenPack metadata, hash it, and compare it to
the lock snapshot. Verification must not execute embedded Python source. Custom
token runtime execution remains governed by profile gates, lock checks, audit
metadata, and explicit user override.

The v0.4 lock hash snapshot reserves token-pack-related hashes:

- `token_spec_hash`
- `token_pack_hash`
- `implementation_ref_hash`
- `runtime_environment_hash`
- `audit_chain_hash`
- `expected_artifact_hash`

Missing packs, mismatched pack hashes, unsupported propagation mode, or
untrusted implementation references are deterministic validation diagnostics.

## Consequences

- P3 `.qstpkg` remains accepted as a legacy package format.
- v0.4 packages can carry TokenPack manifests later without changing P0-P4
  strategy hashes.
- TokenPack source embedding does not create a sandbox guarantee.
- WP0-WP2 only define policy and hash slots. TokenPack registry, package
  embedding, and custom runtime execution remain future work.
