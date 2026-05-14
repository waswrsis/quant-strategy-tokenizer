# QST P2b-0 Basic Mutation Plan

## Goal

Draft the smallest mutation layer for executable repair hints. This is a plan only, not implementation.

## Non-Goals

- No mutation engine in P1
- No schema changes before P2a-0 passes
- No automatic strategy rewrite without explicit command

## Candidate Capabilities

- `qst diff`
- `ChangeParam`
- `InsertBefore`
- executable `repair_hint`
- hash invariant checks before and after mutation

## Required Invariants

- P0 frozen strategies keep the same hashes unless the user explicitly mutates Strategy Content IR.
- Envelope-only changes do not affect graph, param, or instance hash.
- Repair mutations must show before/after hash report.

## Candidate Acceptance

```bash
qst diff left.qst.yaml right.qst.yaml
qst mutate broken.qst.yaml --repair-hint repair.json --output repaired.qst.yaml
qst validate repaired.qst.yaml
qst hash repaired.qst.yaml
```

P2b-0 may start only after P2a-0 has passed its hard gate.
