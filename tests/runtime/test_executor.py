from __future__ import annotations

from pathlib import Path

import pytest

from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.ir.validate import ValidationResult
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file
from quant_strategy_tokenizer.runtime import executor
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from tests.helpers import load_sample_market

ROOT = Path(__file__).resolve().parents[2]


def test_execute_reference_strategy_writes_trace(tmp_path: Path) -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    market = load_sample_market(ROOT / "examples" / "sample_market_btc_15m.csv")
    trace_path = tmp_path / "trace.json"
    result = execute_strategy(ir, {"market": market}, trace_path=trace_path)
    assert result.ok
    assert "plan" in result.outputs
    assert trace_path.exists()
    assert result.trace.error_count == 0
    assert len(result.trace.nodes) == 13


def test_execute_validates_canonical_graph() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    canonical = canonicalize(ir)
    canonical.graph[-1].inputs["decision"] = "missing.decision"
    market = load_sample_market(ROOT / "examples" / "sample_market_btc_15m.csv")

    result = execute_strategy(canonical, {"market": market})

    assert not result.ok
    assert result.error == "validation_failed"
    assert result.validation_failures


def test_unresolved_graph_ref_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    canonical = canonicalize(ir)
    canonical.graph[0].inputs["series"] = "missing.value"
    market = load_sample_market(ROOT / "examples" / "sample_market_btc_15m.csv")

    def validation_ok(_ir: object, **_kwargs: object) -> ValidationResult:
        return ValidationResult()

    monkeypatch.setattr(executor, "validate", validation_ok)
    result = execute_strategy(canonical, {"market": market})

    assert not result.ok
    assert result.error == "missing_input"
    assert result.trace.error_count == 1
