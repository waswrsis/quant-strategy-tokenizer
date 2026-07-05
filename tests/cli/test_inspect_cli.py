from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from qst.cli import app

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "examples" / "strategies" / "01_ema_cross" / "strategy.gkr.yaml"


def test_inspect_combines_validation_identity_receipt_and_admission(tmp_path: Path) -> None:
    output = tmp_path / "ema.canonical.json"
    result = CliRunner().invoke(
        app,
        ["inspect", str(STRATEGY), "--canonical-output", str(output)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"]
    assert payload["validation"]["ok"]
    assert payload["memory_admission"]["allowed"]
    assert payload["strategy_receipt"]["schema_version"] == (
        "qst-strategy-record-receipt/2.0"
    )
    assert payload["strategy_receipt"]["strategy_hash"].startswith("sha256:")
    assert payload["hashes"]["graph_hash"].startswith("sha256:")
    assert payload["canonical"]["output"] == output.as_posix()
    assert output.is_file()


def test_canonicalize_confirms_written_output(tmp_path: Path) -> None:
    output = tmp_path / "ema.canonical.json"
    result = CliRunner().invoke(
        app,
        ["canonicalize", str(STRATEGY), "--output", str(output)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"]
    assert payload["output"] == output.as_posix()
    assert payload["canonical_digest"].startswith("sha256:")
    assert payload["canonical_size"] == output.stat().st_size
