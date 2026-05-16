# Token Authoring

Token authors should define behavior through TokenSpec metadata before adding
implementation references.

## Required Shape

- `token_id` must match `namespace.name`.
- `token_ref` must include namespace, name, version, and behavior version.
- Inputs and outputs must use structured PortSpecs.
- Numeric behavior must declare a numeric policy.
- Risk metadata must be structured and explicit.
- Implementation and runtime references must be canonical JSON-compatible.

## Hash Discipline

Semantic metadata belongs in TokenSpec or PortSpec material. Free-form notes may
exist, but they must not be used to smuggle semantic behavior outside hashes.
