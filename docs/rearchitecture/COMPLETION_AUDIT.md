# QST 1.0 Alpha Completion Audit

## Verdict

QST `1.0.0a1` satisfies the locally defined rearchitecture scope. The candidate is a
deterministic record, evidence, attestation, claim-control, customization, and
human-governed token-incubation layer for financial agents. It is not an execution
runtime.

This audit covers the local branch `research/qst-1.0-agent-provenance`. It does not
claim that the branch, commits, or freeze tags have been published to GitHub.

## Requirement Evidence

| Requirement | Evidence | Result |
|---|---|---|
| Product redefinition and major-version signal | `ADR-0001-qst-1.0-product-redefinition.md`, package version `1.0.0a1` | pass |
| Deterministic token-gap resolution | `qst/resolver/`, frozen resolver policy identity, immutable route lattice, alias/recipe/proposal/profile/policy hashes | pass |
| Evidence, attestation, and claim separation | `qst/evidence/`, `qst/attestations/`, `qst/claims/`, domain-separated identities in `qst/identity/` | pass |
| Efficient artifact recording | content-addressed objects and SQLite WAL index in `qst/storage/`; bounded read-only collectors in `qst/collectors/` | pass |
| AI4Finance workflow coverage | declared adapters in `qst/adapters/ai4finance/`; FinRobot, FinRL, FinRL-X, and Qlib at L3; FinGPT and FinRL-Meta at L2 | pass |
| Agent customization declarations | declared overlays, approval binding, and undeclared-customization rejection in `qst/customization/` | pass |
| Human-governed token design | gap/draft/proposal lifecycle in `qst/incubator/`; contract, implementation, conformance, publication, and activation gates are distinct | pass |
| Publication is not activation | publication approval cannot activate a project-local token; activation requires a separate human-authorized transition | pass |
| Claim policy and receipts | sealed evidence evaluation and experiment/agent receipts in `qst/claims/` and `qst/receipts/` | pass |
| v0.4 compatibility | legacy IR, canonical, token, and hash behavior retained under `qst/compat/v04/`; reference hash tests pass | pass |
| No primary execution surface | legacy custom-token commands are isolated under `qst compat-v04 token`; the QST 1.0 primary CLI has no execution command | pass |
| Tamper and source-integrity rejection | alpha acceptance tests reject tampered identities and NUL-bearing Python sources | pass |
| Bounded identity and response behavior | alpha acceptance performance and response-bound tests pass | pass |

## Adapter Maturity Boundary

- L3 means a declared, tested evidence extractor with golden fixtures. It does not mean
  QST executes the external workflow.
- L2 means a declared record contract with deterministic normalization and tests, but
  not a complete extractor for every upstream output shape.
- External checkpoints, metrics, and result artifacts are collected as content-addressed
  evidence. QST does not train models, run inference, or run trading simulations.

## Local Gate Evidence

- Focused rearchitecture and documentation tests: `20 passed`.
- Full test suite: `589 passed`.
- Coverage suite: `589 passed`; total package coverage `89.67%`.
- Static gates: compileall, Ruff, mypy (`150 source files`), and stateless lint passed.
- Prompt pack and prompt artifact validation passed.
- Coverage matrix validation passed for `120` patterns; the publication frontier check
  passed with its record-layer disclaimers intact.
- Vocabulary validation passed for `6` packs and `179` tokens with zero diagnostics.
- All eight stage manifests validate with zero issues.
- `git diff --check` passed.

## Explicit Non-Goals

The accepted alpha does not train models, run inference, execute backtests, claim
profitability, route orders, connect to brokers or exchanges, provide HFT or production
execution, execute agent-authored token code, or let an agent approve or activate its
own token proposal.

## Freeze Policy

Stages 0 through 7 are frozen by local commits and annotated local tags. Any later
change to a frozen contract requires an explicit supersession record. Publishing the
branch or tags requires separate user authorization.
