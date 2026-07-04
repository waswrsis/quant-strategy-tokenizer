from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from qst.cli import app
from qst.compat.v04 import compute_hashes_v2, load_ir_v04_file, validate_ir_v04

ROOT = Path(__file__).resolve().parents[2]
RUNNER = CliRunner()


def test_primary_cli_has_no_custom_execution_group() -> None:
    result = RUNNER.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "compat-v04" in result.stdout
    assert "token" not in {
        line.strip().split()[0]
        for line in result.stdout.splitlines()
        if line.strip().startswith("token")
    }


def test_legacy_custom_runtime_is_explicitly_namespaced() -> None:
    result = RUNNER.invoke(app, ["compat-v04", "token", "execute", "--help"])
    assert result.exit_code == 0
    assert "legacy v0.4" in result.stdout
    assert RUNNER.invoke(app, ["token", "execute", "--help"]).exit_code != 0


def test_v04_reference_hashes_remain_unchanged() -> None:
    strategy = ROOT / "examples" / "strategies" / "01_ema_cross" / "strategy.gkr.yaml"
    sentinel = json.loads(
        (ROOT / "tests" / "reference" / "strategies" / "01_ema_cross" / "hashes.json").read_text(
            encoding="utf-8"
        )
    )
    ir = load_ir_v04_file(strategy)
    assert validate_ir_v04(ir).ok
    hashes = compute_hashes_v2(ir)
    assert hashes.graph_hash == sentinel["graph_hash"]
    assert hashes.param_hash == sentinel["param_hash"]
    assert hashes.instance_hash == sentinel["instance_hash"]
