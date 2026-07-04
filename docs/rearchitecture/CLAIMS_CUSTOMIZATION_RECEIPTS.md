# Claims, Customization, and Receipts

## Declared Customization

Every semantic override is a sealed `CustomizationDeclaration` with distinct requester
and author, scope, rationale, base identity, JSON Pointer operations, identity impact,
risk, approval requirement, and UTC declaration time. Operations apply to a deep copy.
If approval is required, the caller must provide an approval identity. A candidate that
differs from the declared overlay is rejected as undeclared customization.

Customization changes a derived result identity. It never mutates the accepted base
TokenSpec, strategy, evidence, or adapter record in place.

## Claim Evaluation

Claim policies require evidence payload kinds, counts, verified-result status, and a
minimum adapter maturity. Adapter maturity is accepted only through a sealed
`qst.adapter-verification/1.0` attestation. L2 evidence cannot satisfy an L3 requirement.
The evaluator emits a sealed `ClaimDecision`; it does not execute an experiment or grant
approval.

## Receipt Layers

The identities remain separate:

```text
strategy_hash      = canonical strategy identity
experiment_hash    = strategy + data snapshots + evaluator + parameters + costs + seeds
agent_receipt_hash = experiment + agent/model/tools/prompt/task + approvals + recommendation
```

Changing a seed, cost, data snapshot, model, tool version, approval, or recommendation
changes the corresponding receipt identity without changing the underlying strategy
identity.

## AI4Finance Golden Boundary

FinRobot, FinRL, FinRL-X, and Qlib L3 fixtures may satisfy a workflow-evidence maturity
requirement when their result artifacts and adapter attestation verify. FinGPT and
FinRL-Meta remain L2 and cannot satisfy the same claim. No claim implies profitability,
live execution, broker integration, or production readiness.

