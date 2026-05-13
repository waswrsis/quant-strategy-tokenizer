# Quant Strategy Tokenizer

Quant Strategy Tokenizer is a reference implementation of the construction manual v1.1 with the v1.1.1 patch applied, plus the P1-core extension from `QST_P1_CONSTRUCTION_MANUAL_v1.2.md`.

The current implementation keeps the P0 baseline frozen and adds the P1-core envelope, profile, risk, and order-intent workflow. It does not include P1-extended FSM, TA indicator expansion, max-loss risk controls, or purity/temporal validator work.

The implemented loop covers:

- 25 built-in tokens with behavior contracts
- 8 built-in JSON recipes
- Strategy Content IR loading from YAML
- `_envelope` parsing outside Strategy Content IR
- canonicalization, three-layer hashing, validation, and repair hints
- local execution with trace output
- L1 explanation, trace explanation, agent API, and CLI
- profile promotion from `research` to guarded profiles without changing content hashes

## P1-core Status

P0 frozen baseline:

- 17 tokens
- 4 recipes
- Frozen hashes and vocabulary triples recorded in `docs/P0_ACCEPTANCE.md`

Current P1-core state:

- 25 tokens
- 8 recipes
- P1-core CLI/e2e/docs accepted
- P1-extended not started

Reference strategy:

```bash
python -m quant_strategy_tokenizer.cli validate strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli execute strategies/kdj_cross_basic.qst.yaml --market examples/sample_market_btc_15m.csv
```

P1-core reference strategy:

```bash
python -m quant_strategy_tokenizer.cli validate strategies/examples_kdj_with_ema_filter.qst.yaml --profile research
python -m quant_strategy_tokenizer.cli promote strategies/examples_kdj_with_ema_filter.qst.yaml --to pretrade --output /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml
python -m quant_strategy_tokenizer.cli execute /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml --market examples/sample_market_btc_15m.csv --profile pretrade --trace-path /tmp/qst_p1_trace.json
python -m quant_strategy_tokenizer.cli explain-trace /tmp/qst_p1_trace.json --level human
```

## P0 Verification

Install in editable mode:

```bash
pip install -e ".[dev]"
```

Run the compatibility checks:

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

- `qst vocabulary --check` reports 25 tokens and 8 recipes, while P0 frozen triples remain resolvable.
- `qst validate` exits 0 for the P0 reference strategy.
- `qst hash` prints `graph_hash`, `param_hash`, and `instance_hash`.
- `qst execute` writes the requested trace file.
- `qst compare` keeps `graph_hash` identical when only `lookback` changes, while `param_hash` and `instance_hash` change.
- `qst compare` reports the changed parameter path, for example `recipes.kdj.params.lookback: 9 -> 14`.

## P1-Core Verification

```bash
qst validate strategies/examples_kdj_with_ema_filter.qst.yaml --profile research
qst execute strategies/examples_kdj_with_ema_filter.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --profile research \
  --trace-path /tmp/qst_p1_research_trace.json

qst promote strategies/examples_kdj_with_ema_filter.qst.yaml \
  --to pretrade \
  --output /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml

qst validate /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml --profile pretrade
qst execute /tmp/examples_kdj_with_ema_filter.pretrade.qst.yaml \
  --market examples/sample_market_btc_15m.csv \
  --profile pretrade \
  --trace-path /tmp/qst_p1_trace.json

qst explain-trace /tmp/qst_p1_trace.json --level human
qst explain-trace /tmp/qst_p1_trace.json --level agent
qst explain-trace /tmp/qst_p1_trace.json --level raw
```

Expected behavior:

- Promotion emits a stable JSON result and writes `_envelope.profile: pretrade` when `--output` is provided.
- Promotion does not change the Strategy Content IR hashes.
- Pretrade validation requires a `risk.*` ancestor before `plan.order_intent`.
- Execution produces a trace containing `decision.reduce/v2`, `risk.position_cap`, and `plan.order_intent`.

The project experience from the previous repository history is preserved in [docs/PROJECT_EXPERIENCE.md](docs/PROJECT_EXPERIENCE.md), with its supporting asset at [docs/assets/performance-90d.png](docs/assets/performance-90d.png).
