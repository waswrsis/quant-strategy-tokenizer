# Authority Governance

QST records cryptographic authority evidence without assuming that every record-layer
workflow needs the same enforcement policy. Authority evaluation is therefore
mode-aware and keeps two facts separate:

- `authorized`: whether the supplied registry, signatures, delegation, revocation
  snapshot, scope, and quorum prove authorization;
- `proceed`: whether the selected mode permits the record-layer operation to continue.

An unverified record is never represented as authorized.

## Modes

| Mode | Intended use | Missing or invalid authority evidence |
|---|---|---|
| `record_only` | ingestion, migration, research capture, draft records | record the issue and continue |
| `advisory` | review workflows that want verification feedback | emit findings and continue |
| `enforce` | publication, activation, controlled customization | block the governed operation |

`record_only` is the default because QST is a record layer. Callers must select
`enforce` explicitly at a policy boundary. Structural corruption, stale identities,
and malformed records still fail in every mode; modes do not disable integrity checks.

## Trust Model

- Ed25519 public keys are actor-bound in a sealed `AuthorityRegistry` snapshot.
- Private keys never enter QST records.
- Quorum counts distinct actors, not signatures.
- Rules bind action, role, scope, optional actor allowlists, and human requirements.
- Revocation can target actors, keys, delegation grants, or governance bundles.
- Delegation is signed, scoped, time-bounded, revocable, and non-transitive.
- `authority_delegator` cannot itself be delegated.
- Bundle replay can be rejected by supplying consumed bundle identities.

The registry is a caller-pinned trust snapshot. QST verifies its identity but does not
claim that the registry was distributed by a global certificate authority.

## Governed Entry Points

`qst.authority` provides mode-aware facades for:

- adapter attestations used by claim evaluation;
- human review transitions in the token incubator;
- declared customization approvals.

In `record_only` and `advisory`, an authority decision identity may be retained as the
governance reference even when authorization is false or unknown. Consumers must read
the referenced `AuthorityDecision.authorized` field; an ID alone is not proof of
approval. In `enforce`, the facade applies no governed transition or customization
unless authorization and record binding both pass.

## Usage

```python
decision = authorize_bundle(
    bundle,
    registry,
    evaluated_at=now,
    mode="advisory",
)

assert decision.proceed is True
# This can still be False when advisory findings exist.
print(decision.authorized)
```

Use `mode="enforce"` only where the surrounding product policy requires a gate. Do not
infer runtime, broker, exchange, model execution, or trading authorization from these
record-layer decisions.
