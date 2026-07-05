# Changelog

## 1.0.0a2 FinRobot Provenance Closure

- Replaced public receipt 1.0 models with strict strategy, experiment, and agent receipt
  2.0 identities.
- Added a complete canonical GKR strategy hash while preserving graph, parameter, and
  instance hashes as separate identities.
- Made every `backtested` claim require a sealed experiment receipt with data snapshots,
  date range, costs, slippage, seeds, metric definitions, and verified result evidence.
- Expanded the read-only FinRobot bridge with bounded text/path inspection, canonical
  delivery, stable diagnostics, strategy-memory admission, and backtest admission.
- Added financial-report provenance review gates and a tamper-evident append-only JSONL
  audit export.
- Preserved the no-model, no-backtest, no-broker, no-exchange, and no-live-execution
  product boundary.

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
- Added Stage 11 deterministic JSON/YAML profile persistence, declared project-local
  policy records, builtin impersonation checks, and a non-executing authority CLI.
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
