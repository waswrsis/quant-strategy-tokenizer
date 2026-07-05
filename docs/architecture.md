# Architecture

QST is organized around Graph Kernel Records: typed strategy records with deterministic canonicalization, hashable semantic surfaces, and reference validation artifacts.

## Layers

- `qst.ir`: strategy IR models, canonicalization, validation, and GKR path helpers.
- `qst.types`: TypeSpec parsing and structured value types.
- `qst.ports`: input/output signatures and temporal rules.
- `qst.hash`: graph, parameter, behavior, signature, token, runtime, audit, and expected-artifact hashes.
- `qst.tokens`: TokenSpec, TokenSurfaceSpec, TokenPack, lock metadata, built-in vocabulary, and registry resolution.
- `qst.validation`: diagnostics, validation results, and deterministic validator ordering.
- `qst.profiles`: research, paper, pretrade, and guarded-production policy shells.
- `qst.numeric`: numeric policy and token evolution metadata.
- `qst.state`: delay, accumulate, edge-detect, FSM, and state reference traces.
- `qst.decision`: decision kinds, monoids, fold policies, aggregators, and migration classification helpers.
- `qst.panel`: panel type-layer metadata, panel reference operators, weight operators, and reference validation runners.
- `qst.custom_runtime`: custom-token integrity, local approval, execution grants, audit records, and output validation.
- `qst.provenance` and `qst.evidence`: immutable actors, activities, artifacts, and observations.
- `qst.receipts`: complete-strategy, experiment, and agent receipt 2.0 identities.
- `qst.claims` and `qst.admission`: evidence policy decisions and receipt-backed labels.
- `qst.authority`: mode-aware signatures, quorum, delegation, revocation, and governed transitions.
- `qst.storage`: content-addressed artifacts and rebuildable derived indexing.
- `qst.integrations.finrobot`: bounded read-only agent sidecar operations.
- `qst.report_audit` and `qst.audit_jsonl`: report review gates and tamper-evident audit export.

## Canonical Material

The canonical surface is JSON-compatible and deterministic. Semantic model changes enter the appropriate hash material; trace output and local approval state do not enter strategy identity.

Token surface metadata is canonical TokenSpec material. It changes TokenSpec and
TokenPack hashes, but it does not alter strategy graph or parameter hashes unless
the strategy graph or params themselves change.

Receipt and authority identities use separate versioned domains. They do not enter v0.4
strategy graph/parameter/instance hash material. Typed records and CAS artifacts are the
source of truth; JSONL is a derived append-only audit view.

## Public Artifacts

- Source strategies use `.gkr.yaml`.
- Packaged Graph Kernel Records reserve `.gkr`.
- JSON schemas live in `docs/schemas/` and keep their internal `$id` and `schema_version` values stable.
- Deterministic reference artifacts live in `tests/reference/`.
- Stage 3B token-surface acceptance and gap-review reports live in `docs/reports/`.
