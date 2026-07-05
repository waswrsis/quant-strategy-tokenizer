# Claims, Customization, and Receipts

## Declared Customization

Every semantic override is a sealed `CustomizationDeclaration` with requester, author,
scope, rationale, base identity, JSON Pointer operations, identity impact, risk,
approval requirement, and UTC time. Operations apply to a deep copy. Undeclared or
overlapping changes are rejected.

## Receipt 2.0 Layers

```text
strategy_hash
  = complete canonical GKR in the qst:canonical-strategy:v2 domain

experiment_hash
  = strategy receipt + data snapshots + date range + evaluator + parameters
    + costs + slippage + seeds + metric definitions + result evidence

agent_receipt_hash
  = experiment + agent/model/model-version + tools + prompt/task
    + approvals + output artifacts + recommendation
```

`StrategyRecordReceipt` also retains graph, parameter, and instance hashes. This avoids
overloading one hash with four different identity questions. Receipt 1.0 is not a public
compatibility surface.

## Claim Evaluation

Claim policies require evidence kind/count, verified-result status, and adapter maturity.
Every `backtested` policy additionally requires an ExperimentReceipt 2.0 and a verified
result requirement. The evaluator checks that receipt result IDs refer to sealed,
verified result evidence for the same subject. A custom policy cannot disable this gate.

Adapter maturity is accepted only through a sealed `qst.adapter-verification/1.0`
attestation. L2 cannot satisfy L3. L4 additionally requires a signature artifact. The
evaluator emits a sealed ClaimDecision; it does not execute an experiment or grant
approval.

## Authority Interaction

Claim truth and authority are separate. `record_only` and `advisory` modes may allow an
external workflow to continue collecting records, but they do not turn a denied claim
into an allowed claim. `enforce` mode additionally blocks governed transitions when
authority evidence is insufficient.

## AI4Finance Boundary

FinRobot, FinRL, FinRL-X, and Qlib L3 fixtures may satisfy workflow-evidence maturity
requirements when result artifacts and adapter attestations verify. FinGPT and
FinRL-Meta remain L2. No receipt or claim implies profitability, live execution, broker
integration, or production readiness.
