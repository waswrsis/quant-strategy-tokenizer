# Strategy Coverage Public Statement

QST has reached a measured strategy record-layer raw routable coverage frontier
of 89.70% on the current Coverage Frontier v0.3 benchmark. This headline
includes direct built-in GKR support, partial records, and bounded
custom-token-required routes.

Supporting metrics:

| Metric | Value |
| --- | ---: |
| Headline metric | `routable_record_coverage_raw` |
| Raw routable record coverage | 89.70% |
| Direct built-in coverage | 37.33% |
| Discounted routable record coverage | 85.56% |
| Custom-token route share | 9.23% |
| Boundary false-supported count | 0 |
| Kernel gap count | 12 |

This statement is generated from the auditable Coverage Frontier v0.3 matrix
and report tooling:

```bash
python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --json
python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --check
```

This is record-layer coverage only. It does not include runtime, backtest,
broker, exchange, HFT, optimizer execution, profitability, production execution,
or live trading coverage.
