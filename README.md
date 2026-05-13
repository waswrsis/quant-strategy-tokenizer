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

## P0 Verification

Install in editable mode:

```bash
pip install -e ".[dev]"
```

Run the P0 checks:

```bash
qst vocabulary --check

qst validate strategies/kdj_cross_basic.qst.yaml
qst canonicalize strategies/kdj_cross_basic.qst.yaml
qst hash strategies/kdj_cross_basic.qst.yaml
qst explain strategies/kdj_cross_basic.qst.yaml --level L1

qst execute strategies/kdj_cross_basic.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --trace-path /tmp/qst_trace.json

cp strategies/kdj_cross_basic.qst.yaml /tmp/kdj_lookback_14.yaml
sed -i.bak 's/lookback: 9/lookback: 14/' /tmp/kdj_lookback_14.yaml
qst compare strategies/kdj_cross_basic.qst.yaml /tmp/kdj_lookback_14.yaml
```

Expected behavior:

- `qst vocabulary --check` reports 17 tokens and 4 recipes.
- `qst validate` exits 0.
- `qst hash` prints `graph_hash`, `param_hash`, and `instance_hash`.
- `qst execute` writes the requested trace file.
- `qst compare` keeps `graph_hash` identical when only `lookback` changes, while `param_hash` and `instance_hash` change.
- `qst compare` reports the changed parameter path, for example `recipes.kdj.params.lookback: 9 → 14`.

The project experience from the previous repository history is preserved in [docs/PROJECT_EXPERIENCE.md](docs/PROJECT_EXPERIENCE.md), with its supporting asset at [docs/assets/performance-90d.png](docs/assets/performance-90d.png).
