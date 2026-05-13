#!/usr/bin/env bash
set -euo pipefail

python -m quant_strategy_tokenizer.cli vocabulary --check
python -m quant_strategy_tokenizer.cli validate strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli hash strategies/kdj_cross_basic.qst.yaml
python -m quant_strategy_tokenizer.cli explain strategies/kdj_cross_basic.qst.yaml --level L1
python -m quant_strategy_tokenizer.cli execute strategies/kdj_cross_basic.qst.yaml --market examples/sample_market_btc_15m.csv
