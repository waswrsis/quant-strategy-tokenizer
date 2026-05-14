# ADR: QST Design v2

Date: 2026-05-14

## Status

Draft. This ADR prepares P2 entry but does not start P2 implementation.

## Context

QST is a strategy tokenization system with a frozen P0 baseline, accepted P1-core deployment/profile layer, and P1-extended-a purity/temporal validation.

P0/P1 guarantees:

- P0/P1 hash algorithms remain unchanged.
- P0 token and recipe semantics remain backward compatible.
- P1-core promotion changes the envelope only.
- P1-extended-a validates safety metadata without changing Strategy Content IR hashes.

## Decision

P2 will be planned as a separate construction phase with three conceptual tracks:

- composition layer
- operation layer
- execution optimization

P2a-0 is a mandatory spike gate before any broader P2 work.

## Constraints

- P2 must not back-edit P0/P1 hashes.
- Provenance must not enter `instance_hash`.
- CSE may exist only in an Execution Plan layer, not in canonical Strategy Content IR.
- P2 implementation must use a separate plan and acceptance gate.

## Non-Goals

- No provenance tag implementation in this ADR.
- No TagSpec implementation.
- No recipe generator.
- No CSE/runtime cache.
- No kernel substitution.
- No FSM, expanded indicator library, RL, HFT, plugin, or MCP work.
