# P1-Core Acceptance Record

Date: 2026-05-13
Commit: pending final CI

## Scope

P1-core is implemented. P1-extended is not started.

Included:

- Decision variants `Block` and `Abstain`
- Deployment envelope parsing outside Strategy Content IR
- Profiles `research`, `paper`, `pretrade`, and `production_guarded`
- P1-core token vocabulary and recipes
- Risk-path validation for guarded `plan.order_intent`
- `agent.promote`, `agent.explain_trace`, `qst promote`, and `qst explain-trace`
- Reference strategy `strategies/examples_kdj_with_ema_filter.qst.yaml`

Excluded:

- FSM/state transition engine
- TA indicator expansion beyond P1-core
- `max_loss`
- Purity and temporal validator expansion
- Plugin registry
- MCP adapter

## Frozen P0 Compatibility

P0 frozen values remain unchanged. See `docs/P0_ACCEPTANCE.md`.

Required compatibility gate:

```bash
pytest tests/e2e/test_p0_p1_backward_compat.py
```

Result: pending final CI

## P1-Core Reference Hashes

`strategies/examples_kdj_with_ema_filter.qst.yaml`:

- graph_hash: `sha256:e6da7fcfe5157b30011c7ae178cef3f4a4cd82e9946794d0709fbc7cd8ac7bfa`
- param_hash: `sha256:fb2820dd501cdfce9c058478235f7ba78d2849649c9ba237c144ebec3db52321`
- instance_hash: `sha256:1bcc10844c6bc878e382a3b1dc8524780f34c8ac8d2c1ef603e3074fff3c74a3`

`strategies/examples_kdj_with_ema_filter.pretrade.qst.yaml`:

- Expected profile: `pretrade`
- Expected Strategy Content IR hashes: same as research source
- Expected guarded validation result: pass

## Vocabulary

- P0 frozen tokens: 17
- P0 frozen recipes: 4
- P1-core total tokens: 25
- P1-core total recipes: 8

P1-core additions:

- Tokens: `state.read_field`, `risk.position_cap`, `risk.notional_cap`, `plan.order_intent`, `decision.map_status`, `decision.reduce/v2`, `compare.ge`, `compare.lt`
- Recipes: `event.threshold_above`, `event.threshold_below`, `gate.elapsed_threshold`, `gate.cooldown`

## Local Checks

```bash
ruff check .
mypy quant_strategy_tokenizer tests
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
pytest --cov=quant_strategy_tokenizer --cov-fail-under=80

qst vocabulary --check
qst validate strategies/kdj_cross_basic.qst.yaml
qst hash strategies/kdj_cross_basic.qst.yaml
qst validate strategies/examples_kdj_with_ema_filter.qst.yaml
qst promote strategies/examples_kdj_with_ema_filter.qst.yaml --to pretrade
qst validate strategies/examples_kdj_with_ema_filter.pretrade.qst.yaml
qst execute strategies/examples_kdj_with_ema_filter.pretrade.qst.yaml --market examples/sample_market_btc_15m.csv --trace-path /tmp/qst_p1_trace.json
qst explain-trace /tmp/qst_p1_trace.json --level human
```

Result: pending final CI

## CI

GitHub Actions run: pending final CI
Result: pending final CI

## Notes

- `canonical_version` remains `qst-canonical/0.1`.
- `ir_version` remains `qst-ir/0.3`.
- P1-core promotion changes only the deployment envelope.
