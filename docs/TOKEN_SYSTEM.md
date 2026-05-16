# Token System

The current Token System defines typed, hashable token metadata and deterministic
reference semantics. It is metadata-first: TokenSpec and TokenPack identity are
portable, while execution requires explicit runtime and trust boundaries.

## TokenSpec

A TokenSpec records:

- structured `token_ref`,
- input and output PortSpecs,
- parameter schema,
- numeric policy,
- lifecycle status,
- risk metadata,
- implementation and runtime environment references,
- dependencies and tests.

TokenSpec hashes are computed from canonical structured material. Behavior
version, lifecycle, numeric policy, ports, and risk changes are hash-bearing.

## TokenPack

A TokenPack declares namespaces, tokens, dependencies, origin, and attestation
claims. Attestation claims are not self-trusting; local policy and approval still
decide whether code may run.

## Reference Semantics

The current reference kernel includes:

- temporal validation,
- numeric policy metadata,
- token lifecycle policy,
- state and FSM helpers,
- decision monoids/fold policies/aggregators,
- panel and weight reference helpers,
- custom-token verify/approve/execute boundary.
