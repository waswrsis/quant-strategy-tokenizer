# ADR: Custom Token Runtime Trust Model

Date: 2026-05-15

Status: Accepted

## Context

Token System v2 opens QST to project-local, installed, and community token packs. This is necessary for extensibility, but it changes the trust model. A token can no longer be treated as safe because it is registered. Safety must come from explicit metadata, deterministic hashes, profile gates, package verification, and audit trails.

## Decision

QST v0.1 custom token runtime does not provide a sandbox.

A `python_entrypoint` token executes user-installed Python code. QST treats that as equivalent to running a Python package chosen by the user. The risk is controlled through explicit declarations and gates, not hidden isolation.

Custom tokens must declare:

- type contract
- port temporal contract
- purity and capability requirements
- state behavior
- numeric policy
- implementation reference
- risk level
- attestations
- lifecycle
- tests

## Implementation Reference Hash

`implementation_ref_hash` is computed from the implementation reference kind:

- `spec_only`: canonical TokenSpec v2 bytes
- `source_tree`: deterministic source tree hash
- `wheel`: wheel file SHA-256
- `sdist`: source distribution SHA-256
- `installed_distribution`: installed distribution metadata plus RECORD hashes when present, falling back to installed file bytes when RECORD omits a file hash

Python bytecode is not part of the hash material.

## Trust And Attestation

`trust_tier` cannot be self-declared by a token author.

Effective trust is derived from:

- origin tier: core, project local, installed token pack, community pack
- attestation records
- implementation reference hash
- risk level
- numeric policy
- lifecycle
- profile policy

Attestations are structured records. They may state who reviewed, tested, signed, or approved a token pack, but they do not automatically make the token trusted for every profile.

## Token Pack Equivalence

A pip-installed token pack and an in-tree token pack are equivalent only when their TokenPack manifest, TokenSpec hashes, implementation reference hashes, and audit material match the expected lock or package evidence.

Registry source order for v2 is:

1. project-local token specs
2. installed token packs
3. core registry

Core namespace collision is rejected. Non-core duplicate token refs with the same TokenSpec hash are deduplicated; non-core duplicate token refs with different hashes are rejected except for `user_local` project overrides inside namespaces owned by that project. `user_local` override is a local development convenience and not portable trust for publishable qstpkg artifacts.

## Verify Behavior

Verification outcomes:

- Installed token pack exists and all hashes match: PASS.
- Token pack is embedded in qstpkg and attestation is acceptable for the requested profile: PASS or warning depending on profile policy.
- Token pack is missing: FAIL.
- Token pack hash or implementation reference hash mismatches: FAIL.
- Token risk exceeds the requested profile and no local approval is available: authorization requires approval or is denied by profile, while integrity may still pass.
- Explicit override with acknowledged risk may pass only when the profile policy permits it, `allow_token=true`, `ack_risk=true`, and an audit record is written.

`verify_integrity` never imports, loads entry points from, inspects, or executes the custom distribution. `installed_distribution` evidence records environment identity; incomplete RECORD material may support `environment_recorded` evidence but does not imply bit-exact replayability.

## Audit Location

Custom token audit records are written into package audit material:

```text
qstpkg/audit/
  validation_audit.jsonl
  token_override_audit.jsonl
  runtime_token_audit.jsonl
```

The lock records an `audit_chain_hash` over canonical audit JSONL material.

## Consequences

- QST remains extensible without pretending arbitrary Python is safe.
- Custom token risk becomes visible and reviewable.
- Pretrade and production guarded profiles can block high-risk or unaudited tokens by default.
- Token System v2 verification must understand token pack hashes, implementation reference hashes, attestations, and audit chain hashes.
