# ADR: QST Token System v2 Hash Stability Milestones

Date: 2026-05-15

## Status

Accepted for Token System v2 v1.0.3 planning.

## Context

Token System v2 introduces new hash kinds for `qst-ir/0.4`. Those hashes must
be available early, but freezing them too early would block the schema work that
is still intentionally staged.

## Decision

Hash stability is staged:

- WP1-WP4: v0.4 hashes are provisional.
- WP5 accepted: `signature_hash`, `behavior_hash`, and `token_spec_hash` freeze
  for v0.4-core.
- WP5b accepted: qst.lock and qstpkg propagation material freezes.
- WP9 accepted: `implementation_ref_hash`, `runtime_environment_hash`, and
  `audit_chain_hash` freeze.
- Stage 2B must not change v0.4 core hash kinds.

The v2 hash framework includes:

- `graph_hash`
- `param_hash`
- `instance_hash`
- `signature_hash`
- `behavior_hash`
- `token_spec_hash`
- `token_pack_hash`
- `implementation_ref_hash`
- `runtime_environment_hash`
- `audit_chain_hash`
- `expected_artifact_hash`

## Consequences

Current P0-P4 accepted hashes remain frozen and are not comparable to v0.4
hashes. New v0.4 hashes are separate identities.
