# QST 1.0 Alpha Full Audit

- Audit date: 2026-07-04
- Audited branch: `research/qst-1.0-agent-provenance`
- Baseline: Stage 7 local alpha freeze
- Scope: QST 1.0 contracts, v0.4 compatibility, packaging, tests, and local gates

## Verdict

The audit found correctness defects that the Stage 7 suite did not cover. They were
reproduced with negative tests and repaired in Stage 8. The repaired tree passes the
full local gate set and remains a record/governance layer rather than an execution
runtime.

This is a local engineering audit. It is not an external security certification, a
supply-chain attestation, or a GitHub release review.

## Fixed Findings

### A1: Claim evidence could cross subject and trust boundaries

Severity: high.

The evaluator counted duplicate evidence, did not restrict evidence to the requested
subject, accepted future evidence, accepted unsealed adapter attestations, and checked
only that a policy hash existed rather than that it still matched policy material. An
unsigned L4 maturity statement could also qualify.

Fix: claim evaluation now revalidates policy, evidence, and attestation identities;
deduplicates evidence by identity; filters by subject and evaluation time; binds
attestations to existing subject evidence; and requires a signature artifact for L4.

### A2: Resolver fact evidence and input integrity were incomplete

Severity: high.

Non-canonical invalid input could raise before producing `invalid_intent`. When a request
was both non-goal and reserved, route precedence was correct but `boundary_terms`
discarded the reserved facts. Duplicate recipe/proposal IDs and contradictory runtime
term classes were accepted. A fabricated vocabulary snapshot hash was trusted.

Fix: invalid inputs now produce deterministic fallback identities, boundary terms are
the sorted union of all collected boundary facts, catalogs require unique IDs, policy
term classes are disjoint, and snapshot material is rehashed at resolver construction.

### A3: Artifact and collector trust boundaries accepted stale identities

Severity: high.

A zero chunk size could store an empty digest for a non-empty file. Deduplication checked
only object size, so same-size corruption survived a repeated put. Store, index, and
collector APIs did not consistently revalidate identity-bearing objects after shallow
model mutation.

Fix: chunk size is validated; existing objects are rehashed; descriptor, activity, and
proposal identities are checked at trust boundaries; verified activities and verified
result evidence require stable artifact IDs.

### A4: Claim-adapter verification was too weak

Severity: high.

AI4Finance `verify()` accepted any sealed external record with the adapter ID, without
checking the declared schema, run/subject binding, status, or required complete-result
fields.

Fix: verification now validates the evidence identity, schema, run ID, subject, status,
result shape, and adapter-specific complete-result fields.

### A5: Token lifecycle accepted unsealed snapshots

Severity: medium.

`apply_transition()` accepted an unsealed current proposal, and a directly constructed
proposal history could contain unsealed transitions.

Fix: gap, proposal, and transition identities are revalidated before lifecycle changes;
proposal histories require sealed transitions.

### A6: Customization overlays permitted ambiguous composition

Severity: medium.

Duplicate declarations and parent/child JSON Pointer overlaps could be applied in hash
order, producing deterministic but semantically ambiguous last-writer behavior.

Fix: declarations must be sealed and unique; overlapping paths are rejected within and
across declarations.

### A7: Qlib compatibility import had canonicalization and node-ID gaps

Severity: medium.

Non-finite or unsupported YAML values could escape the loader, and repeated known Qlib
record classes generated duplicate GKR node IDs.

Fix: normalized workflow data must pass canonical JSON validation, unsupported YAML
types and key collisions are rejected, and duplicate records receive stable suffixes
without changing singleton output.

## Verification Evidence

- Focused audit suites cover resolver, evidence, governance, storage, incubator,
  AI4Finance, and Qlib negative paths.
- Full pytest: `606 passed`; coverage: `89.73%`, above the required 85 percent.
- Ruff, mypy, compileall, stateless lint, prompt, coverage-frontier, vocabulary, stage
  manifest, and committed-diff gates pass.
- A PEP 517 wheel builds successfully and contains the expected typed package modules
  without tests.
- Existing public strategy and Qlib singleton fixtures remain unchanged and pass.

## Residual Risks Requiring Product Decisions

These items are not silently implemented because each changes a public trust or
compatibility contract.

1. **Authority registry distribution.** Stage 9 adds mode-aware Ed25519 verification,
   delegation, revocation, and quorum records. A registry remains a caller-pinned trust
   snapshot; global registry distribution, transparency logging, and organizational
   PKI integration remain product decisions.
2. **Deep immutable record values.** Pydantic frozen models are shallow; nested mappings
   can be mutated in memory. Trust-boundary rehashing now rejects stale identities, but
   persistent immutable containers would prevent mutation earlier.
3. **Physical v0.4 isolation.** The primary CLI hides execution under `compat-v04`, but
   legacy executor modules remain in the same distribution and are imported by the CLI
   process. A separate compatibility distribution or lazy plugin boundary would reduce
   capability exposure.
4. **Adapter maturity expansion.** FinGPT and FinRL-Meta remain L2 wrapper-manifest
   adapters. L3 requires upstream-version-specific extractors, golden output bundles,
   and provenance for checkpoint/result canonicalization.
5. **Store/index crash and concurrency protocol.** The local CAS and SQLite WAL index
   are suitable for single-host research use. Multi-process descriptor writes, recovery
   journals, locking, and remote replication are not formalized.
6. **Resolver schema coverage.** Parameter compatibility intentionally implements the
   current deterministic JSON-schema subset. Nested schemas, unions, conditional
   schemas, and coercion policy require a versioned resolver-policy extension.
7. **Claim policy language.** `allow_warnings` has no warning-source model, and policies
   cannot yet name trusted issuer sets, allowed adapter IDs, revocation snapshots, or
   signature algorithms.
8. **Supported-Python matrix.** This audit ran on Python 3.12. The package declares
   Python 3.11+, so clean Python 3.11 CI remains necessary before public 1.0 alpha
   publication.

## Environment Note

The repository wheel built successfully. Global `pip check` reported unrelated broken
`cnocr` extras in the host user environment, so it is not accepted as project dependency
evidence. A clean isolated dependency job is the appropriate publication gate.
