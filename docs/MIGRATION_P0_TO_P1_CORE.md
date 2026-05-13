# Migration From P0 To P1-Core

P1-core is backward compatible with the frozen P0 baseline.

## Existing P0 Strategies

No changes are required for existing P0 strategies:

- `_envelope` is optional.
- Missing `_envelope.profile` defaults to `research`.
- Strategy Content IR canonicalization and hashing are unchanged.
- P0 token and recipe ids remain resolvable.
- P0 CLI commands and flags remain compatible.

## Adding An Envelope

An envelope may be added at the YAML top level:

```yaml
_envelope:
  profile: research
```

This metadata is not part of Strategy Content IR and does not change `graph_hash`, `param_hash`, or `instance_hash`.

## Moving Toward Pretrade

Use `qst promote`:

```bash
qst promote strategies/examples_kdj_with_ema_filter.qst.yaml --to pretrade
```

Before promoting a strategy that emits `plan.order_intent`, make sure the graph contains an upstream `risk.*` token. P1-core provides `risk.position_cap` and `risk.notional_cap`.

## P0 Compatibility Check

Run:

```bash
pytest tests/e2e/test_p0_p1_backward_compat.py
qst vocabulary --check
qst hash strategies/kdj_cross_basic.qst.yaml
```

The P0 `kdj_cross_basic` instance hash must match `docs/P0_ACCEPTANCE.md`.
