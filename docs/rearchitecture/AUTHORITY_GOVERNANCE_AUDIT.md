# Authority Governance Audit

- Audit date: 2026-07-04
- Branch: `research/qst-1.0-agent-provenance`
- Baseline: Stage 8 full-audit hardening freeze
- Scope: Stage 9 authority records, cryptography, policy modes, and integrations

## Verdict

The Stage 9 implementation passes the full local repository gate set after correcting
mode and identity defects found during construction review. Authority is optional at
record-ingestion boundaries and enforceable at explicit policy boundaries. No mode can
turn missing or invalid evidence into an authorized fact.

This is a local engineering audit, not a third-party cryptographic certification or
organizational PKI review.

## Fixed Findings

### G1: Initial authority facades were too strict for a record layer

The first integration shape required registry and bundle inputs and rejected token
transitions or customizations whenever quorum was absent. That made exploratory capture,
migration, and advisory review unnecessarily behave like publication enforcement.

Fix: the public facades now support `record_only`, `advisory`, and `enforce` modes.
`record_only` is the default. `authorized` and `proceed` are independent fields, and
only explicit `enforce` mode blocks a governed operation.

### G2: A manually constructed authorized decision could omit trust bindings

The initial decision model allowed `authorized=True` without registry or bundle
identities. Such a record could be sealed even though it was not anchored to evaluated
authority material.

Fix: an authorized decision now requires both identities, and enforce-mode progression
must exactly match authorization. Negative model tests cover forged combinations.

### G3: Evidence-only claims acquired an unintended authority requirement

The first claim facade initialized authority satisfaction from the presence of
attestations. A valid claim with no attestations could therefore be blocked in enforce
mode even though there was no authority-bearing input to verify.

Fix: authority satisfaction starts true and is reduced only by supplied attestation
records that fail authority verification. Claim-policy results remain separate from
authority results.

## Verified Properties

- Ed25519 signatures bind statement, actor, key, and signing time.
- Quorum counts distinct registered actors and enforces role, scope, allowlist, and
  optional human requirements.
- Actor, key, delegation, and bundle revocations are evaluated deterministically.
- Delegation is scoped, time-bounded, revocable, and non-transitive.
- Replay detection accepts an explicit consumed-bundle identity set.
- Claim, proposal-transition, and customization facades preserve mode semantics.
- Structural corruption and stale identities fail in every mode.
- Existing v0.4 strategy, token, hash, adapter, and coverage-frontier behavior remains
  unchanged.

## Remaining Product Decisions

1. **Registry distribution:** choose local files, organization PKI, transparency log,
   or a signed registry-of-registries. The current registry is caller-pinned.
2. **Policy profiles:** decide whether named profiles should map use cases such as
   ingestion, research review, publication, and activation to the three modes.
3. **Persistence and replay ledger:** decide whether consumed bundles and revocations
   need a transactional store rather than caller-supplied snapshots.
4. **Decision-reference vocabulary:** the legacy customization result field is named
   `approval_ids`; in non-enforcing modes it can reference a decision whose
   `authorized` value is false or unknown. A future schema can rename this to
   `governance_decision_ids` with an explicit migration.
5. **Registry authorization:** decide whether registry snapshots themselves require
   threshold signatures and rotation proofs.

These are intentionally not hidden behind stricter defaults. They change deployment or
public record contracts and should be selected for concrete use cases.
