# Agent Practice Guidance

Agents working on QST should treat the repository as a deterministic language
kernel, not as a playground for runtime experiments.

## Method

1. Read the active docs and relevant tests first.
2. Keep changes scoped to the requested layer.
3. Prefer structured models and canonical helpers.
4. Preserve current hashes unless an ADR explicitly changes them.
5. Run focused tests before broader gates.
6. Do not reintroduce archived history as active behavior.

## Safety Rules

- Do not execute custom token code during integrity verification.
- Do not create portable trust from local approval files.
- Do not use wall-clock calls inside deterministic core paths.
- Do not add broad runtime or adapter behavior without a new ADR.
- Do not silently widen schemas or capability enums.
