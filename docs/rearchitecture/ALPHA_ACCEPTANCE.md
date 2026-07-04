# QST 1.0 Alpha Acceptance

## Candidate Definition

The accepted local candidate is package version `1.0.0a1` on
`research/qst-1.0-agent-provenance`. Its authoritative construction evidence is the
ordered Stage 0-8 manifests and corresponding annotated local freeze tags.

## Required Invariants

- Evidence, attestation, claim decision, customization, and approval remain distinct.
- Resolver identity contains every catalog and policy input that can change routing.
- AI4Finance adapters expose collection and verification, never execution.
- Only L3/L4 adapters may support workflow-evidence maturity claims.
- Agents cannot approve, publish, activate, execute code, or create grants.
- Published project-local tokens require a separate explicit activation sequence.
- Undeclared semantic customization is rejected.
- The primary CLI contains no custom-code executor.
- v0.4 strategy identities and demo sentinels remain unchanged.

## Efficiency Evidence

- Artifact hashing uses bounded 4 MiB reads by default.
- Object writes deduplicate by raw SHA-256 digest.
- SQLite WAL is a derived local index and can be rebuilt from descriptors.
- FinRobot token-resolution responses are constrained by tests to at most 4 KiB.
- Small canonical identity hashing has a local p95 target below 10 ms.

These are record-layer measurements, not model, backtest, or trading performance claims.

## Publication

The candidate commit and all stage tags remain local. GitHub publication is outside this
acceptance and requires explicit user approval.
