# P0 / P1 Boundary

## P0.1 Only Allows Hardening

Allowed:

- e2e roundtrip tests
- runtime unresolved ref strictness
- canonical validation order fix
- README P0 verification
- `qst compare` parameter-path output
- `qst execute --trace-path`
- CI acceptance record
- minor bug fixes that do not expand vocabulary

Not allowed in P0.1:

- new indicators: MACD / RSI / Bollinger / ATR
- new risk tokens
- state / fsm / profile
- `plan.order_intent`
- plugin registry
- `agent.parse` / LLM parser
- MCP adapter
- standalone detokenize

## Entry Criteria For P1

P1 may start only after:

- P0 roundtrip e2e passes
- `qst vocabulary --check` passes
- `qst execute` produces trace
- `qst compare` shows lookback parameter diff
- `docs/P0_ACCEPTANCE.md` records green CI
