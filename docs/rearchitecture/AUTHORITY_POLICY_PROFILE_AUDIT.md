# Authority Policy Profile Audit

- Audit date: 2026-07-04
- Branch: `research/qst-1.0-agent-provenance`
- Baseline: Stage 9 authority governance freeze
- Scope: policy profiles, mode selections, facade integration, and stage tooling

## Verdict

The profile layer preserves non-blocking record capture while making stricter behavior
an explicit use-case decision. Built-in profiles, custom complete profiles, and declared
overrides are deterministic and identity-bearing. Full local gates pass after repairing
two coordination defects found during construction review.

## Fixed Findings

### P1: Stage manifests were ordered lexicographically

The stage validator read filenames in lexical order, placing `stage-10` before
`stage-2`. This incorrectly broke the frozen-prefix check as soon as the first two-digit
stage was added.

Fix: loaded manifests are sorted by parsed integer `stage_id`, with a regression fixture
covering stages 0 through 10.

### P2: Facade results did not enforce profile-selection consistency

The initial profile integration returned both `mode` and `mode_selection` but allowed a
manually constructed result to disagree about the effective mode.

Fix: claim, transition, and customization result models now enforce mode agreement,
authority-decision mode agreement, progression semantics, and applied/result presence.

## Verified Properties

- Every profile defines all seven use cases exactly once.
- Profiles and selections reject stale identities.
- `record-capture` is the default and remains non-blocking.
- Research review can be advisory while publication and activation remain enforced.
- Controlled release enforces customization, publication, and activation.
- A mode-changing override requires a non-empty rationale and changes selection identity.
- Profile choice never changes the underlying signature authorization fact.
- Full strategy, adapter, token, prompt, coverage-frontier, and v0.4 compatibility gates
  remain unchanged.

## Remaining Product Decisions

1. Decide whether applications should reference profiles by embedded record, local
   registry ID, or signed configuration bundle.
2. Decide whether profile changes require a migration record for long-running projects.
3. Decide whether CLI commands should expose `--authority-profile` and declared
   `--mode-override-reason`, or whether profiles remain library-only in the alpha.
4. Decide whether organization-specific profiles belong in QST artifacts or in external
   policy repositories.

No option is selected automatically because each affects deployment and configuration
ownership rather than record correctness.
