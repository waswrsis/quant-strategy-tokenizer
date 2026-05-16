# ADR: QST Cleanline Reset

Date: 2026-05-16 UTC

## Status

Accepted.

## Context

QST has completed project-wide acceptance at commit
`3013d1db5cd8ddb836f0b8a61dceeaeb0d6dc7a8`. The repository now contains both
the current Token System and a large amount of historical phase material,
legacy compatibility surfaces, and versioned implementation names that make the
main path harder for users, maintainers, and agents to understand.

The project has no public compatibility obligation for pre-cleanline APIs. Git
history and the `cleanline-pre-reset-20260516` tag preserve the accepted state
before this reset.

## Decision

QST adopts a cleanline reset.

- QST IR is the only active IR concept after the reset. Internally, active
  schema material remains `qst-ir/0.4` and `qst-canonical/0.4`.
- Historical `qst-ir/0.3` and `qst-ir/0.3.1` are no longer active targets.
- Legacy migration tooling is removed after the known strategy escape migration
  report is produced.
- Backward compatibility tests are removed or rewritten as current reference
  strategy hash sentinels.
- Historical design, construction, audit, and acceptance documents move to
  `docs/archive/` and become non-normative.
- Active documentation describes only the current QST system.
- Future compatibility starts at the cleanline baseline, not at pre-cleanline
  historical stages.

## Hash Sentinel Policy

Reference strategy hash tests are not backward compatibility promises. They are
current-system drift sentinels and protect accepted canonical examples from
accidental semantic changes.

## Non-Goals

- Do not rewrite git history.
- Do not delete history from the repository record.
- Do not change accepted current hash, schema, token, runtime, package, adapter,
  or custom-token trust semantics as part of the reset.
- Do not introduce new strategy semantics.
- Do not retain compatibility wrappers for removed legacy surfaces.

## Rollback

The safety tag `cleanline-pre-reset-20260516` points to the pre-reset accepted
state. Each destructive work package must be revertible to that tag or the
previous recorded cleanline checkpoint.
