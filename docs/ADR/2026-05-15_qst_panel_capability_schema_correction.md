# ADR: QST Panel Capability Schema Correction

Date: 2026-05-15

## Status

Accepted for Token System v2 WP8b.

## Context

WP8a accepted the Panel Detail Design Gate and froze the `TypeSpec` Panel shell. The WP8b Panel Type Layer must enable only type-layer Panel declarations while keeping Panel operators, weight operators, recipes, and runtime execution disabled.

The existing `qst-ir/0.4` capability shell was created before the WP8 staged capability split and only reserved:

- `core`
- `panel`
- `custom_token_runtime`

That is too coarse for WP8b because `panel` would imply more than the type layer.

## Decision

WP8b applies a schema correction to the `qst-ir/0.4` capability enum:

- remove the deprecated umbrella `panel` literal;
- add `panel_type`;
- add `panel_ops`;
- add `panel_weights`;
- add `panel_recipes`.

Only `panel_type` is accepted by WP8b validation. `panel_ops`, `panel_weights`, `panel_recipes`, and `custom_token_runtime` remain rejected until their owning work packages accept them. The umbrella `panel` literal is not part of canonical `qst-ir/0.4`.

This correction does not modify:

- `TypeSpec` fields;
- `qst_typespec_0_4.schema.json`;
- TypeSpec enum/default behavior;
- v0.4 core canonicalization;
- v0.4 hash kind definitions.

## Consequences

Panel type-layer semantics are enabled through `panel_type` without implying Panel operators or recipes.

Panel semantic type metadata is not free metadata. In WP8b it must be output-scoped under:

```text
node.metadata.panel_type_by_output
```

and must enter Panel signature hash material through the typed Panel signature helper.
