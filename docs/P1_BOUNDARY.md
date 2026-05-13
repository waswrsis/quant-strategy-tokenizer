# P1 Boundary

This document freezes the accepted P1-core scope and keeps P1-extended work out of the current baseline.

## P1-Core Allowed

- Decision sum type with `Accept`, `Reject`, `Block`, `Abstain`, `Unknown`, and `ErrorDecision`
- Deployment `_envelope` outside Strategy Content IR
- Profiles `research`, `paper`, `pretrade`, and `production_guarded`
- `state.read_field`
- `risk.position_cap`
- `risk.notional_cap`
- `plan.order_intent`
- `decision.map_status`
- `decision.reduce/v2`
- `compare.ge`
- `compare.lt`
- Profile-aware validation
- Risk-path validation for guarded `plan.order_intent`
- `agent.promote`
- `agent.explain_trace`
- `qst promote`
- `qst explain-trace`
- Reference strategy `strategies/examples_kdj_with_ema_filter.qst.yaml`

## P1-Core Not Allowed

- FSM or state transition engine
- MACD, RSI, Bollinger, ATR, Donchian, or other TA indicator expansion
- `risk.max_loss`
- `risk.drawdown_cap`
- Plugin registry
- LLM parser
- MCP adapter
- `qst diff`
- Mutation or rewrite commands beyond `qst promote` envelope output

## P1-Extended Entry Criteria

P1-extended may start only after:

- `tests/e2e/test_p0_p1_backward_compat.py` passes
- `tests/e2e/test_p1_core_pretrade.py` passes
- `qst vocabulary --check` reports P0 baseline preserved and current 25/8 vocabulary
- `docs/P1_CORE_ACCEPTANCE.md` records green local checks and CI
- P0 frozen hashes in `docs/P0_ACCEPTANCE.md` remain unchanged

## PR Review Checklist

- [ ] No P0 frozen token or recipe behavior changed
- [ ] No canonicalization or hash algorithm changed
- [ ] No P1-extended token, recipe, or validator was introduced
- [ ] P1-core CLI JSON contracts remain compatible
- [ ] P0 and P1-core e2e tests pass
