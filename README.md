# Quant Strategy Tokenizer

P0 implementation of the Quant Strategy Tokenizer construction manual v1.1 with the v1.1.1 patch applied.

The P0 loop covers:

- 17 built-in tokens and behavior contracts
- 4 built-in JSON recipes
- Strategy Content IR loading from YAML
- canonicalization, three-layer hashing, validation, and repair hints
- local execution with trace output
- L1 explanation, agent API, and CLI

Reference strategy:

```bash
python -m quant_strategy_tokenizer.cli validate strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli execute strategies/kdj_cross_basic.qst.yaml --market examples/sample_market_btc_15m.csv
```

The project experience from the previous repository history is preserved in [docs/PROJECT_EXPERIENCE.md](docs/PROJECT_EXPERIENCE.md), with its supporting asset at [docs/assets/performance-90d.png](docs/assets/performance-90d.png).
