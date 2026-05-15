from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app

ROOT = Path(__file__).resolve().parents[2]
KDJ = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"


def test_migrate_ir_cli_writes_v04_outputs(tmp_path: Path) -> None:
    runner = CliRunner()
    output = tmp_path / "kdj_v04.qst.yaml"
    canonical = tmp_path / "kdj_v04.canonical.json"
    lock = tmp_path / "qst-lock-v04.json"

    result = runner.invoke(
        app,
        [
            "migrate-ir",
            str(KDJ),
            "--to",
            "qst-ir/0.4",
            "--output",
            str(output),
            "--canonical-output",
            str(canonical),
            "--lock-output",
            str(lock),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["source_instance_hash"] != payload["target_instance_hash"]

    migrated = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert migrated["ir_version"] == "qst-ir/0.4"
    assert migrated["derived_from"]["kind"] == "ir_migration"
    assert migrated["derived_from"]["source_instance_hash"] == payload["source_instance_hash"]
    assert canonical.exists()
    assert json.loads(lock.read_text(encoding="utf-8"))["lock_version"] == "qst-lock/0.4"


def test_migrate_package_cli_verifies_and_detects_tamper(tmp_path: Path) -> None:
    runner = CliRunner()
    legacy_package = tmp_path / "legacy.qstpkg"
    migrated_package = tmp_path / "migrated.qstpkg"

    packaged = runner.invoke(app, ["package", str(KDJ), "--output", str(legacy_package)])
    assert packaged.exit_code == 0, packaged.output

    migrated = runner.invoke(
        app,
        [
            "migrate-package",
            str(legacy_package),
            "--to",
            "qst-ir/0.4",
            "--output",
            str(migrated_package),
        ],
    )
    assert migrated.exit_code == 0, migrated.output
    migrated_payload = json.loads(migrated.output)
    assert migrated_payload["source_instance_hash"] != migrated_payload["target_instance_hash"]

    verified = runner.invoke(app, ["verify", str(migrated_package)])
    assert verified.exit_code == 0, verified.output
    assert json.loads(verified.output)["ok"] is True

    (migrated_package / "strategies" / "canonical.json").write_text("{}", encoding="utf-8")
    tampered = runner.invoke(app, ["verify", str(migrated_package)])
    assert tampered.exit_code == 1
    tampered_payload = json.loads(tampered.output)
    assert tampered_payload["ok"] is False
    assert any(failure["kind"] == "canonical_ir_tampered" for failure in tampered_payload["failures"])
