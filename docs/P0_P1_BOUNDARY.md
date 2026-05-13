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

## Technical Invariants Locked At P0

P1 PRs **must not modify** the following. Any PR touching them is a breaking change that requires:

- Bumping `canonical_version` (or `ir_version` if structural)
- An ADR in `docs/ADR/`
- Explicit migration plan

### Algorithm Freeze

- `quant_strategy_tokenizer/ir/canonicalize.py`: 5-rule algorithm body unchanged
- `quant_strategy_tokenizer/ir/hashing.py`: three-layer hash function bodies unchanged
- `canonical_version` constant: stays `"qst-canonical/0.1"`
- `ir_version` constant: stays `"qst-ir/0.3"`

### Vocabulary Freeze

- All 17 P0 token `(id, version, behavior_version)` triples remain valid (see `docs/P0_ACCEPTANCE.md`)
- All 4 P0 recipe `(id, version)` pairs remain valid
- P1 may **add** new versions (e.g. `decision.reduce/v2`) but must not modify `v1`
- P1 may **add** new tokens / recipes but must not rename or remove P0 entries
- P1 may add new token definitions in existing P0 token modules when the existing P0 token code paths and behavior contracts remain unchanged

### Schema Freeze

- `docs/JSON_SCHEMAS/token.schema.json`: append-only (P1 may add optional fields, not required ones)
- `docs/JSON_SCHEMAS/recipe.schema.json`: append-only
- `docs/JSON_SCHEMAS/strategy_ir.schema.json`: append-only; the new Deployment Envelope is a **separate** schema (`docs/JSON_SCHEMAS/envelope.schema.json`)

### Behavior Freeze

- `decision.reduce/v1`: only handles Accept/Reject/Unknown/Error; encountering Block/Abstain raises `executor_exception` (no silent handling)
- `plan.noop`: remains registered; not deprecated
- The 6 P0 agent API signatures: unchanged (`discover`, `vocabulary`, `recipes`, `validate`, `execute`, `explain_ir`)
- The 7 P0 CLI commands: existing flags remain compatible (P1 may add new flags as optional with defaults)

### Test Freeze

- The 34 P0 behavior contracts: unchanged
- `tests/e2e/test_p0_roundtrip.py`: must continue passing
- `tests/e2e/test_p0_p1_backward_compat.py` asserts:
  - `kdj_cross_basic` instance_hash equals the P0 value in `docs/P0_ACCEPTANCE.md`
  - `broken_no_lift` produces a repair_hint suggesting `decision.lift_bool`
  - All P0 vocabulary triples still resolve from registries

## How P1 PRs Self-Check

Before merging any P1 PR, author confirms:

- [ ] No existing P0 token behavior in `tokens/computation/{data,window,smooth,math,compare,logic,norm}.py` modified
- [ ] No existing P0 token behavior in `tokens/infrastructure/{decision,plan}.py` modified
- [ ] P1 token additions in existing modules are append-only and have separate contracts
- [ ] No JSON in `recipes/indicators/{ewm,rma,kdj}.json` modified
- [ ] No JSON in `recipes/events/cross_above.json` modified
- [ ] `ir/canonicalize.py`, `ir/hashing.py` not modified
- [ ] `tests/e2e/test_p0_p1_backward_compat.py` passes
- [ ] CI green on Python 3.11 + 3.12
