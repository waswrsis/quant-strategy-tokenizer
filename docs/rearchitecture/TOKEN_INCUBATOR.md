# Token Incubator Governance

The resolver may detect a gap and an agent may author a draft. Neither action registers
a built-in token. Project-local tokens default to an explicit `project.*` namespace,
experimental maturity, and metadata-only execution support.

## Lifecycle

```text
detected -> agent_draft -> statically_validated -> contract_approved
-> implementation_reviewed -> conformance_passed -> publication_approved
-> published_project_local -> explicit_activation_requested -> activation_approved
-> active_for_project -> builtin_candidate
```

Every transition is immutable, hash-bearing, adjacent, timestamped, and carries actor,
evidence, checklist, and reason codes. Rejection is terminal.

## Required Gates

- Static validation: schema, namespace, ports, params, and boundary checks by a system.
- Contract review: semantics, failure modes, numeric, and temporal review by a human.
- Implementation review: source digest, security, and determinism review by a human.
- Conformance: unit, property, and edge-case evidence recorded by a system.
- Publication review: documentation, versioning, and ownership review by a human.
- Activation review: project scope, profile, and lock review by a human.
- Activation: explicit token-pack lock, profile, namespace, and optional implementation ref.

An agent cannot approve, publish, activate, mark a token accepted, create an execution
grant, or add a draft to the core namespace. Publication does not trigger activation.
Activation is project-local and does not mutate `builtin_token_packs()`.

