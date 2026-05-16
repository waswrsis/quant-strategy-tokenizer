# Reference

## Strategy Files

Editable strategy files use `.gkr.yaml`. CLI strategy inputs reject other source suffixes.

```bash
qst validate examples/strategies/kdj_cross_basic.gkr.yaml
qst hash examples/strategies/kdj_with_ema_filter.gkr.yaml
```

## Schemas

Public schema files live in `docs/schemas/`. File names are public product names; internal `$id` and `schema_version` values remain stable.

Important schemas include:

- `ir-0.4.schema.json`
- `type_spec-0.4.schema.json`
- `port_spec-0.4.schema.json`
- `token_spec-0.4.schema.json`
- `token_pack-0.4.schema.json`
- `decision-0.4.schema.json`
- `state_policy-0.4.schema.json`
- `panel_representation-0.4.schema.json`
- `approval_record-0.4.schema.json`
- `execution_grant-0.4.schema.json`

## Reference Data

Deterministic reference material lives under `tests/reference/`:

- `temporal/`
- `state/`
- `panel/`
- `custom_token/kalman/`

These fixtures and traces are conformance material for the current QST tree, not runtime execution logs.

## Numeric Status

Panel and weight helpers define semantic float64 reference behavior. They are deterministic for the provided reference inputs but are not a bit-exact numerical portability claim across every possible runtime.