# QST Profiles

Profiles live in the YAML `_envelope` section. The envelope is parsed with the strategy file, but it is outside Strategy Content IR and does not participate in canonicalization or the three-layer content hashes.

## Supported Profiles

| Profile | P1-core behavior |
|---|---|
| `research` | Default when `_envelope` is absent. No risk-path requirement. |
| `paper` | Simulation profile. Kept separate from `research` for deployment metadata. |
| `pretrade` | Requires every `plan.order_intent` node to have a `risk.*` ancestor. |
| `production_guarded` | Same P1-core risk-path rule as `pretrade`. |

## Promotion

`qst promote` validates the target profile and emits a stable JSON result. Add `--output` to write a promoted YAML file that changes only `_envelope.profile` and envelope metadata:

```bash
qst promote strategies/examples_kdj_with_ema_filter.qst.yaml \
  --to pretrade \
  --output /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml
```

The Strategy Content IR is preserved. Therefore `graph_hash`, `param_hash`, and `instance_hash` remain unchanged across promotion.

## Guarded Risk Path

For `pretrade` and `production_guarded`, a strategy that emits `plan.order_intent` must include an upstream `risk.*` token. If no risk ancestor exists, validation returns `missing_risk_path` with a repair hint suggesting a risk cap before the order intent.
