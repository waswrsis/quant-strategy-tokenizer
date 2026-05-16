# Contributing

QST is in a cleanline baseline. Contributions should preserve current
`qst-ir/0.4` semantics unless an ADR explicitly changes them.

## Ground Rules

- Keep active code focused on the current IR, TokenSpec/TokenPack metadata,
  reference semantics, validation, and custom-token boundaries.
- Do not reintroduce retired compatibility loaders, migration commands, or old
  runtime/package paths.
- Keep generated caches out of the repository.
- Use structured models and canonical JSON helpers instead of ad hoc string
  manipulation.
- Preserve deterministic hashes unless the change includes an ADR and updated
  sentinel evidence.

## Local Checks

Run these before submitting substantial changes:

```bash
python -m compileall quant_strategy_tokenizer
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
python -m pytest tests -q
python -m quant_strategy_tokenizer.cli vocabulary --check
```

Useful smoke checks:

```bash
python - <<'PY'
import quant_strategy_tokenizer
import quant_strategy_tokenizer.ir
import quant_strategy_tokenizer.tokens
import quant_strategy_tokenizer.types
import quant_strategy_tokenizer.validation
import quant_strategy_tokenizer.custom_runtime
print("import smoke ok")
PY

python -m quant_strategy_tokenizer.cli --help
python -m quant_strategy_tokenizer.cli hash strategies/examples/kdj_cross_basic.qst.yaml
```

## Documentation

Active docs describe the current cleanline system. Historical documents belong
under `docs/archive/**` and must not define current behavior.
