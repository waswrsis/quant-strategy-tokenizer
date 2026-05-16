# ADR: QST Panel Layer Detail Design

Date: 2026-05-15

## Status

Accepted for Token System v2 v1.0.3 planning.

## Context

Token System v2 keeps a single active IR, `qst-ir/0.4`, while accepting the
core and panel layers in separate stages. To avoid Stage 2B changing the
`TypeSpec` shape after core hashes have stabilized, WP2 must reserve the Panel
type shell before Panel behavior is implemented.

## Decision

`Panel[T]` is valid as a `TypeSpec` in Stage 2A, but Panel capability and Panel
operators remain disabled until Stage 2B.

The WP2 Panel shell contains these fields:

- `axes`
- `universe`
- `missing_policy`
- `group_spec_ref`
- `selection_kind`
- `weight_constraints`
- `panel_capability_required`

Recommended Stage 2B defaults:

- `GroupSpec`: `static_mapping` and `field_ref`; dynamic mapping is deferred.
- Selection to weight conversion is explicit and separate from weight
  normalization.
- Residualization is single-factor only.
- Missing data uses `UniverseMask` plus sparse logical Panel; no
  `NullableDecimalString` is introduced in v0.4.
- Panel temporal behavior joins input `port_temporal` values.
- `Panel[State]` is a type-shell allowance only; `state.fsm` does not
  auto-broadcast over Panel in v0.4.

## Consequences

Stage 2B may refine validation and behavior, but it must not change the core
`TypeSpec` shape or v0.4 core hash kinds.
