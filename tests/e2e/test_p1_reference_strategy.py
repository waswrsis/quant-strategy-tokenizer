from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file_with_envelope
from quant_strategy_tokenizer.runtime.executor import execute_strategy
from tests.helpers import load_sample_market

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
PRETRADE = ROOT / "strategies" / "examples_kdj_with_ema_filter.pretrade.qst.yaml"
EXPECTED_TRACE = ROOT / "strategies" / "examples_kdj_with_ema_filter.expected_trace.json"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"
runner = CliRunner()


def _externals() -> dict[str, Any]:
    return {
        "market": load_sample_market(MARKET),
        "state": {"current_symbol": 1.0, "current_notional": 0.0},
        "sizing": 1.0,
    }


def test_p1_reference_strategy_research_and_pretrade_execute(tmp_path: Path) -> None:
    market_inputs = _externals()
    expected = cast(dict[str, Any], json.loads(EXPECTED_TRACE.read_text(encoding="utf-8")))

    research_ir, research_envelope = load_strategy_file_with_envelope(STRATEGY)
    research_validation = validate(research_ir, profile=research_envelope.profile)
    assert research_validation.ok, research_validation.failures
    research_result = execute_strategy(
        research_ir,
        market_inputs,
        trace_path=tmp_path / "qst_p1_research.json",
        profile=research_envelope.profile,
    )
    assert research_result.ok, research_result.error

    pretrade_ir, pretrade_envelope = load_strategy_file_with_envelope(PRETRADE)
    pretrade_validation = validate(pretrade_ir, profile=pretrade_envelope.profile)
    assert pretrade_validation.ok, pretrade_validation.failures
    pretrade_result = execute_strategy(
        pretrade_ir,
        market_inputs,
        trace_path=tmp_path / "qst_p1_pretrade.json",
        profile=pretrade_envelope.profile,
    )

    assert pretrade_result.ok, pretrade_result.error
    assert pretrade_result.trace.strategy_instance_hash == expected["strategy_instance_hash"]
    tokens = {node.token for node in pretrade_result.trace.nodes}
    assert set(expected["must_include_tokens"]).issubset(tokens)
    assert pretrade_result.outputs["plan"].kind == expected["expected_output_plan"]["kind"]
    assert pretrade_result.outputs["plan"].blocked is True
    assert pretrade_result.outputs["plan"].reason == "position_cap_exceeded"


def test_p1_reference_strategy_cli_promote_and_explain_trace(tmp_path: Path) -> None:
    promoted = tmp_path / "examples_kdj_with_ema_filter.pretrade.qst.yaml"
    promoted_result = runner.invoke(
        app,
        ["promote", str(STRATEGY), "--to", "pretrade", "--output", str(promoted)],
    )
    assert promoted_result.exit_code == 0
    assert promoted.exists()

    trace_path = tmp_path / "qst_p1_pretrade.json"
    executed = runner.invoke(
        app,
        [
            "execute",
            str(promoted),
            "--market",
            str(MARKET),
            "--trace-path",
            str(trace_path),
        ],
    )
    assert executed.exit_code == 0
    assert trace_path.exists()

    explained = runner.invoke(app, ["explain-trace", str(trace_path), "--level", "human"])
    assert explained.exit_code == 0
    assert "Blocked by risk path" in explained.output
