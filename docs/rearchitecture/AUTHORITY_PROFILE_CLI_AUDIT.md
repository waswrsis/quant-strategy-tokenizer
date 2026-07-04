# Authority Profile Persistence and CLI Audit

- Audit date: 2026-07-04
- Branch: `research/qst-1.0-agent-provenance`
- Baseline: Stage 10 authority policy profile freeze
- Scope: profile file format, IO, declaration metadata, CLI, and negative inputs

## Verdict

The Stage 11 profile surface is suitable for local alpha use. It provides deterministic
profile persistence and inspection without adding approval or execution behavior. Full
local repository gates pass after repairing declaration and parser defects found during
construction review.

## Fixed Findings

### C1: Custom policy lacked ownership declaration

The initial file design could reseal edited policy without recording who declared the
custom profile or why. Altered material could also retain `builtin` origin.

Fix: profile schema `1.1` distinguishes `builtin` and `project_local`. Project-local
profiles require an actor identity and rationale. Persisted builtin profiles must match
the exact built-in profile identity.

### C2: Initial duplicate-key protection used a custom YAML loader

Although based on `SafeLoader`, the custom loader created unnecessary audit ambiguity
and triggered the repository security lint rule.

Fix: YAML is composed with `SafeLoader`, the node graph is checked for duplicate keys,
cycles, and excessive nesting, and data is then read with `safe_load`. JSON duplicate
keys are rejected through `object_pairs_hook`.

### C3: File size validation had a check/read race

The initial implementation checked file size and then reopened the file without a hard
read bound.

Fix: profile input reads at most the configured limit plus one byte and rejects excess
content before decoding.

### C4: Unknown builtin references fell through to path lookup

`builtin:not-a-profile` was interpreted as a local path after builtin lookup failed.

Fix: explicit `builtin:` references now fail deterministically when the ID is unknown.

## Verified Properties

- JSON and YAML round trips preserve profile identity.
- JSON output is byte-deterministic and profile writes are atomic.
- Existing files are not overwritten without an explicit flag.
- Duplicate keys, YAML cycles, excessive nesting, oversize files, stale hashes, and
  builtin impersonation are rejected.
- CLI listing order and JSON output are deterministic.
- Mode override reasons remain mandatory and identity-bearing.
- CLI commands do not sign, approve, grant, publish, activate, or execute operations.

## Remaining Product Decisions

1. Decide whether projects need a conventional pinned path such as
   `.qst/authority/active-profile.json` or should always pass profile references.
2. Decide whether profile updates require signed migration records.
3. Decide whether a local profile catalog needs locking, history, and rollback support.
4. Decide whether profile and registry configuration should be combined in one signed
   deployment bundle or remain independently pinned records.

These are deployment-management choices and are not required for deterministic local
record use.
