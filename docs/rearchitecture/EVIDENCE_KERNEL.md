# Evidence, Attestation, and Claim Kernel

## Separation

QST 1.0 uses four immutable layers:

1. Provenance descriptors identify actors, activities, and opaque artifacts.
2. Evidence envelopes record observations from a source actor or activity.
3. Attestations bind an issuer statement to one or more evidence identities.
4. Claim decisions record the result of applying a claim policy.

Evidence cannot approve itself. An attestation is not a policy decision. A policy
decision is not an execution grant. These distinctions are enforced by separate models
with `extra="forbid"` rather than by a shared generic record.

## Identity Domains

Every identity excludes only its own identity field and includes a versioned domain:

```text
qst:actor:v1
qst:activity:v1
qst:artifact:v1
qst:evidence:v1
qst:attestation:v1
qst:claim-policy:v1
qst:claim-decision:v1
```

The v0.4 graph, parameter, instance, TokenSpec, and TokenPack hash functions are not
changed by this kernel.

## Artifact Rule

`ArtifactDescriptor.digest` is always the digest of the opaque source bytes. A CSV,
Parquet file, model checkpoint, log, or report does not need semantic canonicalization
to become evidence. If an adapter also produces a normalized form, it records a separate
`normalized_digest` and a required normalization identifier. The normalized digest
never replaces the raw digest.

## Activity State

Collectors represent progress as immutable activity snapshots:

```text
discovered -> collecting -> partial -> complete -> verified
                                      \-> failed
```

Each transition creates a new activity identity and may reference the previous snapshot.
Only a verified activity with a stable artifact list may support verified result
evidence. Stage 3 implements and enforces those transitions.

## Time and Ordering

All timestamps must contain a timezone and are normalized to UTC. Collections whose
order has no semantic meaning are sorted and deduplicated before identity calculation.

