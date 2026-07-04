# AI4Finance Evidence Adapters

QST adapters collect declared configuration and existing outputs. They do not import
AI4Finance runtimes, launch jobs, train models, run inference, execute backtests, or
trade. Wrapper manifests make extraction explicit where upstream output layouts are not
stable contracts.

## Maturity

- L0: boundary documentation only.
- L1: plan/config extraction.
- L2: result collection without a complete verified golden workflow.
- L3: verifier plus checked-in golden workflow fixtures.
- L4: externally signed attestation.

Only L3 and L4 adapters are eligible to support a workflow claim. Adapter verification
still does not prove profitability or authorize execution.

| System | Level | Declared evidence |
|---|---:|---|
| FinRobot | L3 | agents, tools, task, material message log, report |
| FinGPT | L2 | model/tokenizer revisions, dataset snapshot, task, inference parameters |
| FinRL-Meta | L2 | environment, processor, state/action/reward descriptors, dates, seed |
| FinRL | L3 | training, testing, simulation activities, checkpoint, metrics, result |
| FinRL-X | L3 | settings, selection/allocation/timing/risk, costs, weights, result |
| Qlib | L3 | model, dataset, records, strategy, recorder, metrics, artifacts |

FinGPT and FinRL-Meta remain L2 because their current wrappers do not establish a full
verified result fixture. Python reward logic is represented by a declared source digest,
not interpreted semantically.

## FinRobot Tools

`FinRobotReadOnlyTools` exposes six compact operations: strategy validation, strategy
identity summary, deterministic token resolution, evidence inspection, artifact
verification, and claim-readiness inventory. Claim readiness deliberately returns
`not_evaluated`; Stage 6 owns claim-policy evaluation.

## Manifest Boundary

`qst-ai4finance-workflow/1.0` manifests are declarations. Artifact paths must remain
inside the manifest directory. Complete runs require artifacts. Opaque files retain raw
byte digests in the Stage 3 object store.

