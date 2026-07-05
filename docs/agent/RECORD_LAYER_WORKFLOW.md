# Record-Layer Workflow

## Purpose

QST records what a strategy is, what an external workflow used and produced, what an
agent concluded, and which authority decision applies. It does not run the model,
backtest, broker, exchange, or report publisher that produced those facts.

## Record Chain

```text
canonical GKR
  -> StrategyRecordReceipt 2.0
  -> external activity and verified result Evidence
  -> ExperimentReceipt 2.0
  -> AgentReceipt 2.0
  -> ClaimDecision 2.0
  -> optional authority decision
  -> append-only JSONL audit export
```

Each arrow is an explicit reference. Evidence is not approval, a receipt is not an
execution grant, and an authority record does not make an unsupported factual claim
true.

## Strategy Admission

1. Load and validate the `.gkr.yaml` record.
2. Canonicalize it with `qst-canonical/0.4`.
3. Compute graph, parameter, instance, and complete canonical strategy hashes.
4. Declare explicit non-goals.
5. Build a sealed `StrategyRecordReceipt`.
6. Call `admit_strategy_memory`; only an admitted record may be labelled validated in
   agent memory.

The complete strategy hash covers canonical metadata as well as graph material. The
three existing strategy hashes remain separate because they answer different identity
questions.

## Experiment Admission

An external evaluator must provide all of the following before QST accepts a
`backtested` label:

- strategy receipt and complete strategy hash;
- content-addressed data snapshot IDs;
- evaluation start and end dates;
- evaluator adapter ID and version;
- explicit parameters, costs, and slippage assumptions;
- at least one deterministic seed;
- metric names and definitions; and
- verified result evidence IDs.

Seal these values in `ExperimentReceipt` 2.0. A `backtested` `ClaimPolicy` must require
both an experiment receipt and verified result evidence. The generic claim evaluator
enforces this rule; a custom policy cannot disable it.

## Agent Recommendation

`AgentReceipt` 2.0 binds an experiment hash to the agent actor, model and model version,
tool versions, prompt/task references, approvals, output artifacts, and recommendation.
It records a recommendation; it does not approve or execute it.

## Authority Modes

Use authority according to the deployment context:

| Mode | Intended use | Effect |
|---|---|---|
| `record_only` | notebooks, research capture | records missing authority without blocking the surrounding workflow |
| `advisory` | collaborative agent review | emits authority findings for a human or orchestrator |
| `enforce` | controlled publication or activation | blocks governed transitions unless signatures, scope, quorum, delegation, and revocation checks pass |

The mode changes authority enforcement, not evidence truth. A failed claim remains a
failed claim in every mode.

## Audit Export

Typed records and CAS artifacts are the source of truth. `qst.audit_jsonl` exports only
record references, artifact hashes, and bounded redacted summaries. Every line includes
a sequence number, previous hash, and line hash. Do not write credentials, prompts with
secrets, raw filings, model weights, or large tool output into JSONL.

## Stop Conditions

Stop and report a boundary rather than weakening the record when:

- a data snapshot cannot be identified;
- costs, slippage, seeds, or metric definitions are unknown;
- a result is not content-addressed or verified;
- a custom token lacks human approval;
- a reserved TypeSpec or runtime is required;
- the request needs broker, exchange, live execution, or a backtest engine; or
- an agent asks to treat its own assertion as evidence or approval.
