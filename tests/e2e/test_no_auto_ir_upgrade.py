from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.qst_lock.io import read_lock

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"
runner = CliRunner()


def test_p3a0_commands_do_not_auto_upgrade_ir_version(tmp_path: Path) -> None:
    source = tmp_path / "strategy.qst.yaml"
    source.write_text(STRATEGY.read_text(encoding="utf-8"), encoding="utf-8")
    before = source.read_text(encoding="utf-8")
    lock_path = tmp_path / "qst.lock"
    canonical_path = tmp_path / "qst.canonical.json"

    locked = runner.invoke(
        app,
        [
            "lock",
            str(source),
            "--output",
            str(lock_path),
            "--canonical-output",
            str(canonical_path),
        ],
    )
    assert locked.exit_code == 0, locked.output

    verified = runner.invoke(
        app,
        ["verify", str(source), "--lock", str(lock_path), "--canonical", str(canonical_path)],
    )
    assert verified.exit_code == 0, verified.output

    assert source.read_text(encoding="utf-8") == before
    assert read_lock(lock_path).ir_version == "qst-ir/0.3"
    assert "qst-ir/0.3.1" not in canonical_path.read_text(encoding="utf-8")


def test_p3a1_package_commands_do_not_auto_upgrade_ir_version(tmp_path: Path) -> None:
    source = tmp_path / "strategy.qst.yaml"
    source.write_text(STRATEGY.read_text(encoding="utf-8"), encoding="utf-8")
    before = source.read_text(encoding="utf-8")
    package_dir = tmp_path / "strategy.qstpkg"
    unpacked_dir = tmp_path / "unpacked"

    packaged = runner.invoke(app, ["package", str(source), "--output", str(package_dir)])
    assert packaged.exit_code == 0, packaged.output

    verified = runner.invoke(app, ["verify", str(package_dir)])
    assert verified.exit_code == 0, verified.output

    unpacked = runner.invoke(app, ["unpack", str(package_dir), "--output", str(unpacked_dir)])
    assert unpacked.exit_code == 0, unpacked.output

    assert source.read_text(encoding="utf-8") == before
    assert read_lock(package_dir / "qst.lock").ir_version == "qst-ir/0.3"
    assert "qst-ir/0.3.1" not in (package_dir / "strategies" / "canonical.json").read_text(
        encoding="utf-8"
    )
    assert "qst-ir/0.3.1" not in (
        unpacked_dir / "strategies" / "source.qst.yaml"
    ).read_text(encoding="utf-8")


def test_qst_fork_is_only_p3_command_that_outputs_031(tmp_path: Path) -> None:
    output = tmp_path / "forked.qst.yaml"

    forked = runner.invoke(
        app,
        ["fork", str(STRATEGY), "--new-id", "ewm_variant", "--out", str(output)],
    )

    assert forked.exit_code == 0, forked.output
    assert "qst-ir/0.3.1" in output.read_text(encoding="utf-8")
