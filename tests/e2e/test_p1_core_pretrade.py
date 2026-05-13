from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

ROOT = Path(__file__).resolve().parents[2]
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
P0_STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"

runner = CliRunner()


def test_p1_core_research_to_pretrade_cli_roundtrip(tmp_path: Path) -> None:
    research_trace = tmp_path / "qst_p1_research_trace.json"
    pretrade_yaml = tmp_path / "examples_kdj_with_ema_filter.pretrade.qst.yaml"
    pretrade_trace = tmp_path / "qst_p1_pretrade_trace.json"

    research_valid = runner.invoke(
        app,
        ["validate", str(P1_STRATEGY), "--profile", "research"],
    )
    assert research_valid.exit_code == 0, research_valid.output

    research_executed = runner.invoke(
        app,
        [
            "execute",
            str(P1_STRATEGY),
            "--market",
            str(MARKET),
            "--profile",
            "research",
            "--trace-path",
            str(research_trace),
        ],
    )
    assert research_executed.exit_code == 0, research_executed.output
    assert research_trace.exists()

    promoted = runner.invoke(
        app,
        [
            "promote",
            str(P1_STRATEGY),
            "--to",
            "pretrade",
            "--output",
            str(pretrade_yaml),
        ],
    )
    assert promoted.exit_code == 0, promoted.output
    promote_payload = json.loads(promoted.output)
    assert promote_payload["ok"] is True
    assert promote_payload["target_profile"] == "pretrade"
    assert promote_payload["validation_failures"] == []
    assert pretrade_yaml.exists()

    pretrade_valid = runner.invoke(
        app,
        ["validate", str(pretrade_yaml), "--profile", "pretrade"],
    )
    assert pretrade_valid.exit_code == 0, pretrade_valid.output

    pretrade_executed = runner.invoke(
        app,
        [
            "execute",
            str(pretrade_yaml),
            "--market",
            str(MARKET),
            "--profile",
            "pretrade",
            "--trace-path",
            str(pretrade_trace),
        ],
    )
    assert pretrade_executed.exit_code == 0, pretrade_executed.output
    assert pretrade_trace.exists()

    for level in ("human", "agent", "raw"):
        explained = runner.invoke(app, ["explain-trace", str(pretrade_trace), "--level", level])
        assert explained.exit_code == 0, explained.output


def test_p1_core_promote_failure_reports_json_repair_hint() -> None:
    failed = runner.invoke(app, ["promote", str(P0_STRATEGY), "--to", "pretrade"])

    assert failed.exit_code == 1
    payload = json.loads(failed.output)
    assert payload["ok"] is False
    assert payload["target_profile"] == "pretrade"
    assert payload["validation_failures"][0]["kind"] == "missing_risk_path"
    assert payload["validation_failures"][0]["repair_hint"]
