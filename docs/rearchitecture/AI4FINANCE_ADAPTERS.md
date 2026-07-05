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

Verification requires a sealed evidence identity, the declared workflow schema, a
matching run subject, a known status, a result mapping, and all adapter-specific result
fields for complete runs.

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

`FinRobotReadOnlyTools` exposes six compact registration operations: strategy validation,
strategy identity and canonical delivery, deterministic token resolution, evidence
inspection, artifact verification, and claim-readiness inventory. It also exposes
explicit strategy-record, strategy-memory admission, and backtest-admission methods for
an orchestrator that chooses to call them. Claim readiness deliberately returns
`not_evaluated`; only receipt-backed claim evaluation can admit a label.

Inputs are bounded to 1 MiB. Canonical output is inline through 256 KiB and otherwise
stored in CAS. The bridge emits stable diagnostics for unsupported/custom tokens,
missing data/risk records, and the non-executable adapter boundary.

## Manifest Boundary

`qst-ai4finance-workflow/1.0` manifests are declarations. Artifact paths must remain
inside the manifest directory. Complete runs require artifacts. Opaque files retain raw
byte digests in the Stage 3 object store.
