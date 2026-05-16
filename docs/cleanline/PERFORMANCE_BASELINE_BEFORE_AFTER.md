# Performance Baseline Before / After

This report records local Stage R smoke timings and is not a semantic contract.

## Before

The pre-reset state is captured in:

- `docs/cleanline/PRE_RESET_WORKTREE_DIFF.patch`
- `docs/cleanline/PRE_RESET_WORKTREE_DIFF_STAT.txt`
- `docs/cleanline/PRE_RESET_STATUS.txt`
- `docs/cleanline/CLEANLINE_INVENTORY_RAW.txt`

## After

Local Stage R smoke and regression commands completed on the cleanline working
tree:

```text
python -m compileall quant_strategy_tokenizer
PASS

python -m ruff check .
PASS

python -m mypy quant_strategy_tokenizer
PASS

python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
PASS

python -m pytest tests -q
347 passed

python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=85 -q
347 passed, total coverage 88.50%

python -m quant_strategy_tokenizer.cli vocabulary --check
PASS

python -m quant_strategy_tokenizer.cli hash strategies/examples/kdj_cross_basic.qst.yaml
instance_hash sha256:56fd90013048a81f9be6e2bc13adbf732c23f01c275a05ff598f6f9b9df67f25
```
