# Contributing

This repository follows the P0 construction manual v1.1 with the v1.1.1 patch, plus the P1-core scope from `QST_P1_CONSTRUCTION_MANUAL_v1.2.md`.

P0 is a frozen compatibility baseline. P1-core changes may add new tokens, recipes, schemas, CLI flags, and agent APIs, but they must not alter P0 token behavior, P0 recipe definitions, canonicalization, hashing, or the frozen hashes recorded in `docs/P0_ACCEPTANCE.md`.

## Quality Gates

Run these before committing:

```bash
ruff check .
mypy quant_strategy_tokenizer tests
pytest --cov=quant_strategy_tokenizer --cov-fail-under=80
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer/
```

The P0 backward-compatibility test is a hard gate:

```bash
pytest tests/e2e/test_p0_p1_backward_compat.py
```

## Registry Rules

- Production code reads token specs through `get_registry()`.
- Production code reads recipes through `get_recipe_registry()`.
- Tests must not mutate global registries.
- Temporary tokens use `isolated_registry`.
- Temporary recipes use `isolated_recipe_registry`.
- New P1 tokens may be appended, but P0 `v1` token specs and behavior contracts remain frozen.
- New P1 recipes may be appended, but P0 recipe JSON remains frozen.

## P1-Core Scope

Allowed in P1-core:

- Decision variants `Block` and `Abstain`
- Deployment envelope parsing outside Strategy Content IR
- Profiles `research`, `paper`, `pretrade`, and `production_guarded`
- Risk-path validation for guarded order-intent strategies
- P1-core vocabulary and recipes listed in `docs/TAXONOMY.md`
- `agent.promote`, `agent.explain_trace`, `qst promote`, and `qst explain-trace`

Not allowed in P1-core:

- FSM/state transition engine
- New TA indicators beyond the P1-core manual scope
- `max_loss` risk token
- Purity or temporal validator expansion
- Plugin registry
- LLM parser or MCP adapter

## Stateless Lint

Stateless lint is a best-effort guardrail, not a formal effect system. Local false positives can be disabled with:

```python
# qst-lint: disable-next-line -- deterministic test clock stub
```

The reason after `--` is required for review.
