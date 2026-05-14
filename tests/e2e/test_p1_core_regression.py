from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.tokens.registry import get_registry

ROOT = Path(__file__).resolve().parents[2]
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
P0_STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"
runner = CliRunner()


def test_p1_promote_success(tmp_path: Path) -> None:
    output = tmp_path / "pretrade.qst.yaml"

    result = runner.invoke(
        app,
        ["promote", str(P1_STRATEGY), "--to", "pretrade", "--output", str(output)],
    )

    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert payload["ok"] is True
    assert payload["target_profile"] == "pretrade"
    assert output.exists()


def test_p1_promote_missing_risk_path_fails() -> None:
    result = runner.invoke(app, ["promote", str(P0_STRATEGY), "--to", "pretrade"])

    payload = json.loads(result.output)
    assert result.exit_code == 1
    assert payload["ok"] is False
    assert payload["validation_failures"][0]["kind"] == "missing_risk_path"
    assert payload["validation_failures"][0]["repair_hint"]


def test_p1_pretrade_execute_success(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.json"

    result = runner.invoke(
        app,
        [
            "execute",
            str(P1_STRATEGY),
            "--market",
            str(MARKET),
            "--profile",
            "pretrade",
            "--trace-path",
            str(trace_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert trace_path.exists()


def test_p1_trace_contains_risk_block(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.json"
    result = runner.invoke(
        app,
        [
            "execute",
            str(P1_STRATEGY),
            "--market",
            str(MARKET),
            "--profile",
            "pretrade",
            "--trace-path",
            str(trace_path),
        ],
    )
    assert result.exit_code == 0, result.output

    trace = json.loads(trace_path.read_text(encoding="utf-8"))

    assert any(node["token"] == "risk.position_cap" for node in trace["nodes"])
    assert trace["outputs"]["plan"]["kind"] == "noop"
    assert trace["outputs"]["plan"]["blocked"] is True


def test_plan_order_intent_accept_to_order_intent() -> None:
    token = get_registry().get("plan.order_intent")

    result = token.executor(
        decision={"kind": "accept", "reason": "entry"},
        sizing=2.0,
        side="long",
    )

    plan = result.values["plan"].model_dump(mode="json")
    assert plan["kind"] == "order_intent"
    assert plan["sizing"] == 2.0
    assert plan["side"] == "long"


def test_plan_order_intent_block_to_noop_blocked() -> None:
    token = get_registry().get("plan.order_intent")

    result = token.executor(
        decision={
            "kind": "block",
            "reason": "position_cap_exceeded",
            "severity": "critical",
            "evidence": {"current_position": 1.0},
        },
        sizing=2.0,
        side="long",
    )

    plan = result.values["plan"].model_dump(mode="json")
    assert plan["kind"] == "noop"
    assert plan["blocked"] is True
    assert plan["reason"] == "position_cap_exceeded"
