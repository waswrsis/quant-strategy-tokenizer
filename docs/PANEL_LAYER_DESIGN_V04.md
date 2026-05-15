# Panel Layer Design v0.4

Date: 2026-05-15

Status: WP8a accepted design gate

## Scope

WP8a freezes the Panel layer design for later Token System v2 work. It is a design and schema gate only.

WP8a adds:

- Panel representation draft schema.
- Universe mask draft schema.
- Missing policy draft schema.
- Group specification draft schema.
- SelectionPanel and WeightPanel wire boundary draft schema.
- Panel temporal join and Panel state boundary draft schema.
- Schema hash evidence for each WP8a draft.

WP8a does not add Panel runtime behavior, Panel operators, Panel TokenSpecs, TokenPacks, recipe registration, migration tooling, or v0.4 CLI authoring. It also does not enable the `panel` capability.

## TypeSpec Shape Freeze

WP8a does not edit `quant_strategy_tokenizer.types_v2.TypeSpec`.

The accepted WP2 Panel shell field set remains exactly:

- `axes`
- `universe`
- `missing_policy`
- `group_spec_ref`
- `selection_kind`
- `weight_constraints`
- `panel_capability_required`

If a later Panel design requires additional TypeSpec fields, WP8a must fail and a WP2 correction ADR must authorize the shape change. WP8a is not allowed to silently extend TypeSpec.

## Panel Representation

The initial Panel representation is `sparse_logical`.

`sparse_logical` is a representation and universe-membership model. It is not a missing-value policy. Sparse logical Panels require an explicit UniverseMask so the system can distinguish out-of-universe members from missing in-universe values.

## UniverseMask

`UniverseMask=false` means the member is outside the logical universe for that timestamp or context. It is not a missing value.

MissingPolicy only applies when `UniverseMask=true` and the value is absent.

## MissingPolicy

MissingPolicy handles missing data inside the active universe.

Accepted WP8a policy values:

- `error_on_missing`
- `drop_missing`
- `propagate_missing`

The default policy is `error_on_missing`.

WP8a does not introduce `NullableDecimalString`.

## GroupSpec

WP8a accepts two group-specification forms:

- `static_mapping`
- `field_ref`

`dynamic_mapping` is deferred and rejected by the WP8a schema.

`static_mapping` requires:

- `group_id`
- `mapping_ref`
- `mapping_hash`
- `missing_group_policy`
- `group_label_type`

`field_ref` requires:

- `group_id`
- `field_path`
- `missing_group_policy`
- `group_label_type`

`missing_group_policy` defaults to `error` and may also be `drop` or `assign_unknown`.

Group labels are canonical strings in WP8a. Future work may introduce richer group label typing only through an explicit design update.

## SelectionPanel And WeightPanel

`SelectionPanel` and `WeightPanel` are separate wire concepts.

`SelectionPanel` means a selection result. It does not express final portfolio weights.

`WeightPanel` means a weight result. It can be `raw` or `normalized`.

The future conversion boundary is:

- `selection.to_weights`: converts selection results to raw weights.
- `weight.normalize_*`: normalizes raw weights into portfolio-ready weights.

WP8c may emit raw weights. WP8d owns normalization, market-neutral constraints, gross/net targets, and per-symbol caps.

## Residualize

`panel.residualize/v1` is single-factor only:

- input `panel`: `Panel[float]`
- input `factor`: `TimeSeries[float]`
- output `residual`: `Panel[float]`

Multi-factor residualization and `FactorPanel` are deferred.

## Panel Temporal Join

Panel operators use the input port-temporal join formula unless a later operator-specific ADR overrides it:

- `output.unsafe_future = any(input.unsafe_future)`
- `output.available_at = max_available_at(inputs)`
- `output.latency_bars = max(input.latency_bars)`
- `output.min_history_bars = max(input.min_history_bars, operator_required_history)`

For cross-sectional operators with no rolling requirement, `operator_required_history = 0`.

For `panel.residualize/v1`, output temporal metadata is the join of the panel input and the factor input.

## Panel And State

`Panel[State]` remains a type shell only in WP8a.

`state.fsm` does not auto-broadcast over Panel members in v0.4. Any per-symbol FSM behavior requires an explicit future design and implementation stage.

## Schema Hash Evidence

WP8a schema hashes are SHA-256 over deterministic schema bytes:

```text
json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

The QST runtime canonical JSON depth limit is intentionally not used for these draft JSON Schemas because schema documents may contain deeper validation structure than runtime artifacts.

| Schema | Hash |
|---|---|
| `qst_panel_representation_0_4.schema.json` | `sha256:ed2fea8886b9a229b71b86ebaf5b4a717cf14e8e0cf4b23fcaebac192df66588` |
| `qst_panel_universe_mask_0_4.schema.json` | `sha256:f171e4f4c1a0702835606c1100fc2bf0e93a31a632bb89c00aada8a0329f1e32` |
| `qst_panel_missing_policy_0_4.schema.json` | `sha256:2d32d215dee76458e08c695d14e9e138ad1df2b1cf0da99caead012d2a457481` |
| `qst_panel_group_spec_0_4.schema.json` | `sha256:b44d24f02e29cdc73a22becacbe392f761b24c734c0c31e2ea13364131209b4f` |
| `qst_panel_selection_weight_0_4.schema.json` | `sha256:baff36b907bdf7fafe400bf881866af2b87444d3e3fc78cd14906837edac9155` |
| `qst_panel_temporal_state_0_4.schema.json` | `sha256:1cedea73f3d006e533aa3586455fb88e6f64924e313b90a914353bfe39566362` |
| `qst_typespec_0_4.schema.json` | `sha256:f181ce889c24abc36bb57cc5662b50669331b68f2000e7df0dbe6c42647207fd` |

## Boundary

WP8a freezes design boundaries for future work:

- WP8b may implement Panel type-layer behavior only after this gate.
- WP8c may implement Panel operators.
- WP8d may implement weight operators.
- WP8e may implement Panel recipes and PV-B.
- WP9 owns custom token runtime.
- WP10 owns migration tooling.

