from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
P1_STRATEGY = ROOT / "strategies" / "examples_kdj_with_ema_filter.qst.yaml"
MARKET = ROOT / "examples" / "sample_market_btc_15m.csv"
EXPECTED_TRACE = ROOT / "strategies" / "examples_kdj_with_ema_filter.expected_trace.json"
runner = CliRunner()


def test_qst_package_verify_unpack_roundtrip(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    unpacked_dir = tmp_path / "unpacked"

    packaged = runner.invoke(app, ["package", str(STRATEGY), "--output", str(package_dir)])
    assert packaged.exit_code == 0, packaged.output
    package_payload = json.loads(packaged.output)
    assert package_payload["ok"] is True
    assert package_payload["verification_level"] == "STRUCTURAL"

    verified = runner.invoke(app, ["verify", str(package_dir)])
    assert verified.exit_code == 0, verified.output
    verify_payload = json.loads(verified.output)
    assert verify_payload["ok"] is True
    assert verify_payload["verification_level"] == "STRUCTURAL"

    unpacked = runner.invoke(app, ["unpack", str(package_dir), "--output", str(unpacked_dir)])
    assert unpacked.exit_code == 0, unpacked.output
    assert (unpacked_dir / "qst.lock").exists()
    assert (unpacked_dir / "strategies" / "canonical.json").exists()


def test_qst_package_with_expected_trace_verifies_semantic_trace(tmp_path: Path) -> None:
    package_dir = tmp_path / "p1.qstpkg"

    packaged = runner.invoke(
        app,
        [
            "package",
            str(P1_STRATEGY),
            "--output",
            str(package_dir),
            "--market",
            str(MARKET),
            "--expected-trace",
            str(EXPECTED_TRACE),
        ],
    )
    assert packaged.exit_code == 0, packaged.output

    verified = runner.invoke(app, ["verify", str(package_dir)])
    assert verified.exit_code == 0, verified.output
    payload = json.loads(verified.output)
    assert payload["ok"] is True
    assert payload["verification_level"] == "SEMANTIC_TRACE"
