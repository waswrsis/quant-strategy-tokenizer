# Resolver Policy 1.0

## Purpose

The resolver answers one question: can a structured token intent be represented by the
current vocabulary, a declared recipe, an existing proposal, a reserved future type, or
an out-of-scope runtime? It never invents a token and never asks an LLM to choose among
deterministic candidates.

## Two-Phase Evaluation

Phase A collects every relevant fact without routing:

- exact identifier, explicit alias, and requested version matches;
- input and output port names;
- TypeSpec equality;
- parameter-schema compatibility;
- target-profile support;
- Recipe catalog matches;
- existing governed proposals;
- reserved type and non-goal runtime requirements.

The resolver rejects duplicate recipe/proposal IDs and contradictory runtime policy
classes. It rehashes vocabulary snapshot material before use. Invalid Python input that
cannot enter canonical JSON still produces a deterministic `invalid_intent` result
instead of escaping as a serializer exception.

Type and parameter checks are sibling facts. Neither can short-circuit the other, so
changing their implementation order cannot change the route.

Phase B evaluates the immutable `qst-resolver-policy/1.0` lattice:

```text
invalid_intent
-> non_goal_runtime
-> reserved_typespec
-> direct_token_match
-> recipe_match
-> existing_proposal
-> new_token_gap
```

Non-goal and reserved boundaries precede token matches because an existing metadata
token cannot turn external execution or a reserved type system into supported runtime
behavior. Direct tokens precede recipes because they are the smallest accepted record.
Recipes precede proposals because recipes use published vocabulary. Existing proposals
precede new gaps to avoid duplicate design work.

A recipe is eligible only when its declared input/output TypeSpecs, parameter schema,
target profile, and referenced published tokens are all compatible. A matching concept
alone is insufficient.

Changing this order requires a new resolver-policy schema version. It is not a runtime
configuration knob in policy 1.0.

Route precedence selects one route, but does not discard sibling facts. For example, a
request that requires both live execution and `EventStream` routes to `non_goal_runtime`
while retaining both non-goal and reserved terms in `boundary_terms`.

## Candidate Ordering

Candidates are sorted by:

```text
status rank, namespace, name, version, behavior version, TokenSpec hash
```

The status rank is hash-bearing resolver policy material. Resolver matching is
case-sensitive and exact. Natural-language interpretation belongs upstream and must
produce a structured `TokenIntent` before this resolver is called.

## Resolver Identity

A decision identity includes independent hashes for:

- token intent;
- vocabulary snapshot;
- alias catalog;
- recipe catalog;
- proposal catalog;
- profile policy;
- resolver policy;
- complete collected facts and final route.

An alias, recipe, proposal, profile, or policy change therefore cannot reuse an old
resolution identity.

## Compatibility Semantics

- Declared port sets must match candidate port sets exactly.
- Declared TypeSpecs must be structurally equal.
- Omitted input/output requirements mean unspecified, not incompatible.
- Parameter validation supports the deterministic schema subset used by current
  TokenSpecs: required fields, properties, additional properties, JSON primitive types,
  enum, minimum, and maximum.
- A reserved-design token produces `reserved_typespec`, not a direct match.
- Runtime requirements produce `non_goal_runtime` unless policy explicitly classifies
  them as evidence-only collection (`workflow_discovery`, `result_collection`, or
  `artifact_collection`), even if a similarly named token exists.
