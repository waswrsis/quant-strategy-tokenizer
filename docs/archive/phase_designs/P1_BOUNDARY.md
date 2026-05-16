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

## P1-Core Freeze

P1-core is accepted. The following semantics are frozen unless an ADR explicitly authorizes change:

- Decision 6 variants
- `decision.reduce/v2` status priority
- `plan.order_intent` non-Accept behavior
- risk_path validator semantics
- promote modifies envelope only
- pretrade requires risk path
- `qst promote` JSON output shape
- `qst explain-trace` levels

No new indicators, FSM tokens, drawdown tokens, provenance tags, recipe generators, CSE, or kernel substitution may be added under P1-core.

## P1-Extended-A Freeze

P1-extended-a is limited to:

- purity validator
- temporal safety validator
- validation warnings for research/paper temporal risk
- validation failures for strict profile purity/temporal risk

P1-extended-a does not add provenance, recipe generators, CSE, kernel substitution, new indicators, FSM, risk.max_loss, or drawdown controls.

## P1-Extended-B Entry Criteria

P1-extended-b may start only after:

- `tests/e2e/test_p0_p1_backward_compat.py` passes
- `tests/e2e/test_p1_core_pretrade.py` passes
- `qst vocabulary --check` reports P0 baseline preserved and current 25/8 vocabulary
- `docs/P1_CORE_ACCEPTANCE.md` records green local checks and CI
- `docs/P1_EXTENDED_A_VALIDATORS.md` records green local checks
- P0 frozen hashes in `docs/P0_ACCEPTANCE.md` remain unchanged

## PR Review Checklist

- [ ] No P0 frozen token or recipe behavior changed
- [ ] No canonicalization or hash algorithm changed
- [ ] No P1-extended token, recipe, or validator was introduced
- [ ] P1-core CLI JSON contracts remain compatible
- [ ] P0 and P1-core e2e tests pass
