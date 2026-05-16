# Changelog

## Repository Cleanup and README Rewrite

- Removed construction-plan leftovers, stage-level acceptance journals, old
  boundary notes, and local cache artifacts from the submit candidate.
- Rewrote README as the primary user and maintainer entry point for the accepted
  QST project.
- Updated contributing guidance to point at final acceptance records and current
  quality gates.
- Preserved final project acceptance evidence, Token System v2 acceptance
  evidence, ADRs, JSON schemas, fixtures, expected artifacts, tokenpacks, tests,
  and the project background material.
- No code, schema, hash, token, runtime, qstpkg, adapter, migration, or trust
  semantics changed.

## QST Project-Wide Acceptance

- Recorded project-wide acceptance for the P0-P4 foundation and Token System v2
  WP0-WP10.
- Added final acceptance artifacts for project status, Token System v2 status,
  hash stability, security boundaries, and known limitations.
- This was a documentation, evidence, and status update only.

## Token System v2 Finalization

- Accepted `qst-ir/0.4` and `qst-canonical/0.4` as the active v2 kernel target.
- Preserved legacy `qst-ir/0.3` and `qst-ir/0.3.1` as load, verify, explain,
  and migration inputs.
- Added the v2 hash framework, TypeSpec and PortSpec models, temporal
  validation, numeric policy, TokenSpec and TokenPack metadata, state and FSM
  reference semantics, decision algebra, panel and weight reference semantics,
  custom-token runtime boundaries, and legacy migration tooling.
- Added P-Validate reference artifacts for temporal, state, panel, and
  custom-token behavior.

## Legacy P0-P4 Foundation

- Preserved the frozen P0 baseline and compatibility hashes.
- Accepted guarded validation, provenance, mutation, CSE, deterministic locks,
  qstpkg packages, package verification, search, fork lineage, P4 artifact
  schemas, frames, qstpkg artifact references, Universal Port protocols, mock
  adapters, and P4b CLI surfaces.
- Real broker, exchange, vectorbt, qlib, ccxt, mlflow, and backtrader adapters
  remain out of repository scope.
