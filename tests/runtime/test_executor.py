from __future__ import annotations

from pathlib import Path

import pandas as pd

from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.runtime.executor import execute_strategy

ROOT = Path(__file__).resolve().parents[2]


def test_execute_reference_strategy_writes_trace(tmp_path: Path) -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    market = pd.read_csv(ROOT / "examples" / "sample_market_btc_15m.csv")
    trace_path = tmp_path / "trace.json"
    result = execute_strategy(ir, {"market": market}, trace_path=trace_path)
    assert result.ok
    assert "plan" in result.outputs
    assert trace_path.exists()
    assert result.trace.error_count == 0
    assert len(result.trace.nodes) == 13
