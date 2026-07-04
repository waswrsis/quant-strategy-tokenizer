# Changelog

## 1.0.0a1 Agent Provenance Candidate

- Redefined QST as a deterministic strategy identity, evidence, claim-control, and
  token-governance layer for financial agents.
- Added domain-separated provenance, evidence, attestation, claim, customization,
  experiment receipt, and agent receipt records.
- Added streaming content-addressed storage, rebuildable local indexing, and read-only
  AI4Finance evidence adapters.
- Added deterministic token-gap resolution and human-governed project-local token
  incubation with publication separated from activation.
- Preserved v0.4 GKR/hash/token behavior and isolated the legacy custom executor under
  the explicit `compat-v04` CLI namespace.
- Added Stage 8 full-audit hardening for resolver, claim, evidence, artifact, collector,
  adapter, token-incubator, customization, and Qlib negative paths.
- Added Stage 9 Ed25519 authority records, scoped quorum, non-transitive delegation,
  revocation, and switchable `record_only`, `advisory`, and `enforce` policy modes.
- Added Stage 10 use-case authority profiles and auditable mode overrides for ingestion,
  migration, claims, token governance, and customization.
- Kept the candidate local; no GitHub branch, tag, or release was created.

## Stage 3A Token Surface Completion

- Added TokenSurfaceSpec metadata and token contract fields to TokenSpec.
- Added deterministic built-in TokenPack vocabulary entrypoint and token conformance gates.
- Added public token-surface demo strategies with validation artifacts and hash sentinels.
- Documented token family maturity, execution support, and hash impact boundaries.
- No broad runtime, broker, backtester, optimizer engine, IR, or canonical hash algorithm change was introduced.

## Public Product Tree Reset

- Renamed the public Python package to `qst` while keeping the distribution name `quant-strategy-tokenizer`.
- Standardized editable strategy files on the `.gkr.yaml` suffix and reserved `.gkr` for packaged Graph Kernel Records.
- Moved public examples, custom-token material, schemas, and deterministic reference fixtures into the product tree layout.
- Rewrote active documentation around the current product boundary.
- No IR, canonical, hash, token, panel, state, decision, or custom-runtime semantics were intentionally changed.
