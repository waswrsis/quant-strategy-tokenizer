# Coverage Taxonomy

## Coverage Classes

Every strategy pattern must be classified as exactly one class.

### supported

Use only when current built-in token/schema/profile behavior can express the strategy and
a valid `.gkr.yaml` example can be produced. A supported pattern must be mechanically
falsifiable through:

```text
qst validate
qst hash
qst canonicalize
```

No unsupported runtime capability may be hidden in metadata.

### partially_supported

Use when the core strategy record can be expressed, but one or more non-core features must
be represented as explicit limitations. Do not silently weaken the strategy intent.

### custom_token_required

Use when missing signal, model, transform, panel factor, or risk logic can be represented
through a declared custom-token interface with clear ports and output policy. This route
does not imply approval, grant issuance, or execution.

### reserved

Use when the strategy requires a reserved design surface such as EventStream, HFT runtime,
same-bar execution feedback, Distribution-like runtime, or order-book event replay.

### non_goal

Use when the strategy requires broker integration, exchange routing, live order placement,
custody, production execution, full backtest engine, or trading infrastructure.

## Benchmark Groups

- `internal_matrix`: QST-owned strategy patterns and examples.
- `external_benchmark`: strategy intents extracted from public or canonical sources.
- `user_submitted`: user-provided patterns, when available.
- `dogfood`: hard internal QST use cases.

## Coverage Layers

- `intent_routing`: correct classification of pattern intent.
- `direct_builtin_gkr`: supported with built-in token/schema surface.
- `partial_record`: recordable with explicit limitations.
- `custom_token_route`: recordable through bounded custom-token interface.
- `reserved_boundary`: correctly rejected as reserved design.
- `non_goal_boundary`: correctly rejected as outside QST scope.

## External Benchmark Stratification

The first external benchmark seed must include at least one pattern from each category:

```text
indicator_rule
mean_reversion
trend_following
breakout
state_gate
panel_factor
weight_record
custom_signal
custom_model
reserved_event_stream
non_goal_execution
```

If a category cannot be sourced, record:

```yaml
missing_external_category:
  category:
  reason:
  search_or_review_notes:
```

Do not fill the external benchmark only with simple indicator-rule strategies.

