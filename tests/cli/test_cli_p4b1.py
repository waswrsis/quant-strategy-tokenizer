from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.frames import MarketFrame, OHLCVBar, compute_frame_hash
from quant_strategy_tokenizer.frames.io.csv_io import write_csv_frame
from quant_strategy_tokenizer.frames.io.json_io import read_json_frame, write_json_frame
from quant_strategy_tokenizer.package import package_strategy

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
runner = CliRunner()


def _market_frame() -> MarketFrame:
    return MarketFrame(
        bars=[
            OHLCVBar(
                timestamp="2026-05-14T00:00:00Z",
                symbol="BTC/USDT",
                open="100",
                high="101",
                low="99",
                close="100",
                volume="1",
            ),
            OHLCVBar(
                timestamp="2026-05-14T00:01:00Z",
                symbol="BTC/USDT",
                open="100",
                high="102",
                low="100",
                close="101",
                volume="2",
            ),
            OHLCVBar(
                timestamp="2026-05-14T00:02:00Z",
                symbol="BTC/USDT",
                open="101",
                high="103",
                low="101",
                close="102",
                volume="3",
            ),
        ]
    )


def test_cli_adapter_list_and_verify() -> None:
    listed = runner.invoke(app, ["adapter", "list"])
    assert listed.exit_code == 0, listed.output
    descriptors = json.loads(listed.output)
    ids = {descriptor["adapter_id"] for descriptor in descriptors}
    assert "mock-csv-market" in ids
    assert "mock-backtest" in ids

    verified = runner.invoke(app, ["adapter", "verify", "mock-execution"])
    assert verified.exit_code == 0, verified.output
    payload = json.loads(verified.output)
    assert payload["ok"] is True
    assert payload["capabilities"]["execution"] is True


def test_cli_load_market_writes_hashed_market_json(tmp_path: Path) -> None:
    source = tmp_path / "market.csv"
    output = tmp_path / "market.json"
    write_csv_frame(_market_frame(), source)

    result = runner.invoke(
        app,
        [
            "load",
            "market",
            "--source",
            str(source),
            "--symbols",
            "BTC/USDT",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    loaded = read_json_frame(output)
    assert isinstance(loaded, MarketFrame)
    assert loaded.frame_hash == compute_frame_hash(loaded)
    assert loaded.symbols == ["BTC/USDT"]


def test_cli_backtest_builds_verifiable_package(tmp_path: Path) -> None:
    market_path = tmp_path / "market.json"
    package_dir = tmp_path / "result.qstpkg"
    write_json_frame(_market_frame(), market_path)

    result = runner.invoke(
        app,
        [
            "backtest",
            str(STRATEGY),
            "--adapter",
            "mock",
            "--market",
            str(market_path),
            "--output",
            str(package_dir),
        ],
    )
    verified = runner.invoke(app, ["verify", str(package_dir)])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["verification_ok"] is True
    assert (package_dir / "artifacts" / "backtest" / "backtest_evidence.json").exists()
    assert verified.exit_code == 0, verified.output
    assert json.loads(verified.output)["ok"] is True


def test_cli_submit_and_poll_execution_write_reports(tmp_path: Path) -> None:
    plan = tmp_path / "plan.json"
    submit_output = tmp_path / "submit_report.json"
    poll_output = tmp_path / "poll_report.json"
    plan.write_text(
        json.dumps(
            {
                "kind": "order_intent",
                "decision": {"kind": "accept", "reason": "test"},
                "side": "long",
                "sizing": 1.0,
            }
        ),
        encoding="utf-8",
    )

    submitted = runner.invoke(
        app,
        [
            "submit-plan",
            str(plan),
            "--adapter",
            "mock-execution",
            "--confirm",
            "--client-order-id",
            "cid-1",
            "--output",
            str(submit_output),
        ],
    )
    assert submitted.exit_code == 0, submitted.output
    submit_payload = json.loads(submitted.output)
    report_id = submit_payload["report"]["artifact_id"]
    assert submit_output.exists()

    polled = runner.invoke(
        app,
        [
            "poll-execution",
            report_id,
            "--adapter",
            "mock-execution",
            "--output",
            str(poll_output),
        ],
    )

    assert polled.exit_code == 0, polled.output
    poll_payload = json.loads(polled.output)
    assert poll_payload["report"]["artifact_id"] != report_id
    assert poll_payload["report"]["event_type"] == "trade"
    assert poll_output.exists()


def test_cli_track_package_outputs_artifact_ref(tmp_path: Path) -> None:
    package_dir = tmp_path / "strategy.qstpkg"
    package_strategy(STRATEGY, package_dir)

    result = runner.invoke(
        app,
        [
            "track",
            str(package_dir),
            "--adapter",
            "mock-experiment",
            "--run-name",
            "smoke",
            "--tag",
            "stage=p4b-1",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["artifact_ref"]["path"].startswith("artifacts/experiments/")
