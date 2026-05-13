# P0 Acceptance Record

Date: 2026-05-13
Accepted commit: 1827625eea165af47fb6f2fb797db1aba7c64368

## Local Checks

```bash
python -m ruff check .
python -m mypy quant_strategy_tokenizer
python -m pytest --cov=quant_strategy_tokenizer --cov-fail-under=80

qst vocabulary --check
qst validate strategies/kdj_cross_basic.qst.yaml
qst canonicalize strategies/kdj_cross_basic.qst.yaml
qst hash strategies/kdj_cross_basic.qst.yaml
qst explain strategies/kdj_cross_basic.qst.yaml --level L1
qst execute strategies/kdj_cross_basic.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --trace-path /tmp/qst_trace.json
qst compare strategies/kdj_cross_basic.qst.yaml /tmp/kdj_lookback_14.yaml
python -m quant_strategy_tokenizer.lint.stateless quant_strategy_tokenizer
```

Result: PASS

## CI

GitHub Actions run: https://github.com/waswrsis/Quant-Strategy-Tokenizer/actions/runs/25818386598
Result: PASS

Jobs:

- lint
- typecheck
- test (Python 3.11)
- test (Python 3.12)

## Notes

- P0.1 hardening patches applied.
- P1 has not started.
- P0 vocabulary remains frozen at 17 tokens and 4 recipes.
