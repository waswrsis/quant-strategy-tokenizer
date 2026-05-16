# P1-Core Acceptance Record

Date: 2026-05-13
Accepted implementation commit: 644751e73ebe45a97022435281d9d497a2f84834

## Scope

P1-core library layer is implemented. P1-core CLI/e2e/docs are accepted. P1-extended-a was added afterward as a pre-P2 validator hardening step. P1-extended-b is not started.

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
- Plugin registry
- MCP adapter

## Frozen P0 Compatibility

P0 frozen values remain unchanged. See `docs/P0_ACCEPTANCE.md`.

Required compatibility gate:

```bash
pytest tests/e2e/test_p0_p1_backward_compat.py
```

Result: PASS

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
mypy --strict quant_strategy_tokenizer
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
pytest --cov=quant_strategy_tokenizer --cov-fail-under=80

qst vocabulary --check
qst validate strategies/kdj_cross_basic.qst.yaml
qst hash strategies/kdj_cross_basic.qst.yaml
qst validate strategies/examples_kdj_with_ema_filter.qst.yaml --profile research
qst execute strategies/examples_kdj_with_ema_filter.qst.yaml --market examples/sample_market_btc_15m.csv --profile research --trace-path /tmp/qst_p1_research_trace.json
qst promote strategies/examples_kdj_with_ema_filter.qst.yaml --to pretrade --output /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml
qst validate /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml --profile pretrade
qst execute /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml --market examples/sample_market_btc_15m.csv --profile pretrade --trace-path /tmp/qst_p1_trace.json
qst explain-trace /tmp/qst_p1_trace.json --level human
qst explain-trace /tmp/qst_p1_trace.json --level agent
qst explain-trace /tmp/qst_p1_trace.json --level raw
```

Result: PASS

Observed local result:

- `python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80`
- 133 passed
- Coverage: 85.77%

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25824730331
Result: PASS

Jobs:

- lint: PASS
- typecheck: PASS
- test (3.11): PASS
- test (3.12): PASS

## Notes

- `canonical_version` remains `qst-canonical/0.1`.
- `ir_version` remains `qst-ir/0.3`.
- P1-core promotion changes only the deployment envelope.

## After P1-Extended-A

P1-core remains accepted.

P1-extended-a added:

- purity validator
- temporal safety validator
- research/paper temporal warnings
- pretrade/production_guarded purity and temporal failures

P0 / P1-core compatibility:

- PASS

P1-extended-a CI:

- https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25859822444
- Result: PASS

P1-extended-b and P2 remain deferred.
