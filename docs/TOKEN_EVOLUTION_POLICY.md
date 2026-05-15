# Token Evolution Policy

Date: 2026-05-15

Status: accepted for Token System v2 WP4.

## Scope

This document freezes the v0.4 token behavior evolution rules before TokenSpec v2 and TokenPack loading are implemented.

## Behavior Version Rules

- `behavior_version` never changes silently.
- Any output-changing bug fix bumps `behavior_version`.
- Old `behavior_version` records remain verifiable after newer behavior versions are introduced.
- `known_bug` and `deprecated` lifecycle states produce audit warnings.
- New recipes must not default to deprecated token behavior.
- `blocked` token behavior is a hard error in `pretrade` and `production_guarded`.

## Lifecycle States

| State | Meaning | Default profile handling |
|---|---|---|
| `active` | Current accepted behavior. | allowed |
| `deprecated` | Still verifiable, not a default for new recipes. | warning |
| `known_bug` | Preserved for reproducibility but known to be flawed. | warning in research/paper, error in guarded profiles |
| `blocked` | Must not be used for guarded execution. | error |

## Numeric Policy Coupling

Token behavior material must include a `numeric_policy` declaration. Numeric policy is part of the behavior hash material because changes to representation, determinism level, reduction order, `NaN` handling, or infinity handling may alter observable outputs.

Unknown or platform-dependent numeric policy is high risk:

- `research` / `paper`: warning
- `pretrade` / `production_guarded`: error

## Non-Scope

WP4 does not implement TokenSpec v2 registry resolution, TokenPack loading, recipe migration, runtime execution, or custom token execution.
