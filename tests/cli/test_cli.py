from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

ROOT = Path(__file__).resolve().parents[2]
runner = CliRunner()


def test_cli_vocabulary_check() -> None:
    result = runner.invoke(app, ["vocabulary", "--check"])
    assert result.exit_code == 0
    assert "17 tokens" in result.output


def test_cli_validate_and_broken_hint() -> None:
    good = runner.invoke(app, ["validate", str(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")])
    assert good.exit_code == 0
    bad = runner.invoke(app, ["validate", str(ROOT / "strategies" / "broken_no_lift.qst.yaml")])
    assert bad.exit_code == 1
    assert "type_mismatch" in bad.output


def test_cli_hash_compare_explain_execute(tmp_path: Path) -> None:
    strategy = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"
    market = ROOT / "examples" / "sample_market_btc_15m.csv"
    hashed = runner.invoke(app, ["hash", str(strategy)])
    assert hashed.exit_code == 0
    assert "graph_hash" in hashed.output
    compared = runner.invoke(app, ["compare", str(strategy), str(strategy)])
    assert compared.exit_code == 0
    assert "identical" in compared.output
    explained = runner.invoke(app, ["explain", str(strategy), "--level", "L1"])
    assert explained.exit_code == 0
    assert "Strategy: kdj_cross_basic" in explained.output
    with runner.isolated_filesystem(temp_dir=tmp_path):
        executed = runner.invoke(app, ["execute", str(strategy), "--market", str(market)])
        assert executed.exit_code == 0
        assert "trace.json" in executed.output
