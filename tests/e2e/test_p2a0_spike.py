from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
runner = CliRunner()


def test_agent_explain_folds_indicator_ewm_provenance() -> None:
    result = runner.invoke(app, ["explain", str(STRATEGY), "--level", "agent"])

    assert result.exit_code == 0, result.output
    assert "indicator.ewm v1" in result.output
    assert "smooth.linear_recursive" not in result.output
