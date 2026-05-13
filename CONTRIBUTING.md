# Contributing

This P0 repository follows the construction manual v1.1 and the v1.1.1 patch.

Quality gates:

```bash
ruff check .
mypy quant_strategy_tokenizer/
pytest --cov=quant_strategy_tokenizer --cov-fail-under=80
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer/
```

Registry rules:

- Production code reads token specs through `get_registry()`.
- Production code reads recipes through `get_recipe_registry()`.
- Tests must not mutate global registries.
- Temporary tokens use `isolated_registry`.
- Temporary recipes use `isolated_recipe_registry`.

Stateless lint is a best-effort guardrail, not a formal effect system. Local false positives can be disabled with:

```python
# qst-lint: disable-next-line -- deterministic test clock stub
```

The reason after `--` is required for review.
