from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.runtime.trace import Trace, TraceNode
from tests.ir.p1_fixtures import P1_MISSING_RISK_PATH_YAML, P1_PRETRADE_READY_YAML

runner = CliRunner()


def test_cli_promote_success_writes_pretrade_yaml(tmp_path: Path) -> None:
    strategy = tmp_path / "ready.qst.yaml"
    strategy.write_text(P1_PRETRADE_READY_YAML, encoding="utf-8")
    output = tmp_path / "ready.pretrade.qst.yaml"

    result = runner.invoke(app, ["promote", str(strategy), "--to", "pretrade", "--output", str(output)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["target_profile"] == "pretrade"
    assert payload["validation_failures"] == []
    assert payload["output"] == str(output)
    assert output.exists()
    assert "pretrade" in output.read_text(encoding="utf-8")


def test_cli_promote_failure_reports_risk_hint(tmp_path: Path) -> None:
    strategy = tmp_path / "missing.qst.yaml"
    strategy.write_text(P1_MISSING_RISK_PATH_YAML, encoding="utf-8")

    result = runner.invoke(app, ["promote", str(strategy), "--to", "pretrade"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["validation_failures"][0]["kind"] == "missing_risk_path"
    assert payload["validation_failures"][0]["repair_hint"]
    assert "risk.position_cap" in result.output


def test_cli_validate_profile_override(tmp_path: Path) -> None:
    strategy = tmp_path / "missing.qst.yaml"
    strategy.write_text(P1_MISSING_RISK_PATH_YAML, encoding="utf-8")

    research = runner.invoke(app, ["validate", str(strategy), "--profile", "research"])
    pretrade = runner.invoke(app, ["validate", str(strategy), "--profile", "pretrade"])

    assert research.exit_code == 0
    assert pretrade.exit_code == 1
    assert "missing_risk_path" in pretrade.output


def test_cli_explain_trace_levels(tmp_path: Path) -> None:
    trace = Trace(
        run_id="test",
        strategy_instance_hash="sha256:" + "1" * 64,
        ir_version="qst-ir/0.3",
        canonical_version="qst-canonical/0.1",
        nodes=[
            TraceNode(
                id="risk",
                token="risk.position_cap",
                token_version=1,
                behavior_version=1,
                status="ok",
                output_summary={
                    "decision": {
                        "kind": "Block",
                        "value": {
                            "kind": "block",
                            "reason": "position_cap_exceeded",
                            "severity": "critical",
                        },
                    }
                },
            )
        ],
    )
    trace_path = tmp_path / "trace.json"
    trace_path.write_text(trace.model_dump_json(), encoding="utf-8")

    human = runner.invoke(app, ["explain-trace", str(trace_path), "--level", "human"])
    agent = runner.invoke(app, ["explain-trace", str(trace_path), "--level", "agent"])
    raw = runner.invoke(app, ["explain-trace", str(trace_path), "--level", "raw"])

    assert human.exit_code == 0
    assert "Blocked by risk path" in human.output
    assert agent.exit_code == 0
    assert '"token": "risk.position_cap"' in agent.output
    assert raw.exit_code == 0
    assert '"run_id": "test"' in raw.output
