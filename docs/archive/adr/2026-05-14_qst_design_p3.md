# ADR: QST P3 Lock And Portability Entry

Date: 2026-05-14

## Status

Accepted for WP-P3a-0 implementation.

## Context

P0/P1/P2 are accepted with frozen Strategy Content IR semantics, stable canonicalization, and stable three-layer hashes. P3 needs a portable artifact boundary, but the first gate must prove deterministic lock material before package, search, or fork features begin.

## Decision

WP-P3a-0 introduces a canonical JSON `qst.lock` and structured verification result.

The lock records:

- QST version and strict version policy
- IR and canonical versions
- graph, param, and instance hashes
- canonical IR hash
- externals schema hash
- token, recipe, and TagSpec dependency snapshots
- optional fixture hashes

All lock bytes are canonical JSON. YAML lock examples are intentionally forbidden.

## Verification Level

`qst verify` returns `VerifyResult` with:

- `ok`
- `verification_level`
- `limitation_note`
- `failures`

P3a-0 verification is structural. It does not claim numerical output equivalence.

## Boundaries

WP-P3a-0 does not implement:

- package format
- search index
- fork lineage
- `qst-ir/0.3.1`
- new token or recipe vocabulary
- canonical/hash algorithm changes

`qst_version_policy=same_minor` is parsed but explicitly unsupported in P3a-0.

## Compatibility

P3a-0 must preserve:

- P0 frozen hash baselines
- P1-core hash baselines
- P2 provenance, mutation, CSE, and kernel-spike behavior
- `qst-ir/0.3`
- `qst-canonical/0.1`
