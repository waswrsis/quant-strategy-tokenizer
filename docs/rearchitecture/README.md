# QST 1.0 Rearchitecture

QST 1.0 is a deliberate product redefinition. It retains the useful v0.4 strategy
identity and token contracts while adding evidence, attestation, claim control,
deterministic token-gap resolution, and human-governed token incubation.

The target product is a record and governance layer for financial agents. It does not
train models, execute backtests, route orders, connect to brokers or exchanges, or
replace the runtimes from which it collects evidence.

## Construction Order

1. Stage 0: baseline, product ADR, compatibility boundary, and freeze protocol.
2. Stage 1: deterministic resolver policy and route proof.
3. Stage 2: evidence, attestation, and claim kernel.
4. Stage 3: artifact store, collectors, index, and performance baseline.
5. Stage 4: AI4Finance evidence adapters and adapter maturity gates.
6. Stage 5: token-gap evidence, agent drafts, review, publication, and activation.
7. Stage 6: customization declarations, claim policy, and golden workflows.
8. Stage 7: v0.4 migration, tamper and performance acceptance, and alpha candidate.
9. Stage 8: full audit, negative-path repair, and trust-boundary hardening.

Each stage must pass its declared gates before the next stage starts. A completed stage
is saved in a local commit and frozen with an annotated local tag. Nothing is pushed
without explicit user approval.

Stages 0 through 8 are frozen. The audited candidate remains local until the user
explicitly authorizes publication.

## Authoritative Documents

- [Product redefinition ADR](ADR-0001-qst-1.0-product-redefinition.md)
- [Stage governance](STAGE_GOVERNANCE.md)
- [v0.4 compatibility boundary](V04_COMPATIBILITY_BOUNDARY.md)
- [Alpha acceptance](ALPHA_ACCEPTANCE.md)
- [Completion audit](COMPLETION_AUDIT.md)
- [Full alpha audit](FULL_AUDIT.md)
- [Stage manifests](stages/)
