from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.package import (
    add_artifact_to_package,
    package_strategy,
    verify_package,
)
from quant_strategy_tokenizer.qst_lock import sha256_bytes
from tests.package._artifact_helpers import backtest_evidence, execution_report, write_json

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"


def _failure_kinds(package_dir: Path) -> set[str]:
    return {failure.kind for failure in verify_package(package_dir).failures}


def test_verify_package_reports_artifact_json_hash_mismatch(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = write_json(tmp_path / "report.json", execution_report())
    added = add_artifact_to_package(package_dir, report)

    write_json(package_dir / added.artifact_path, execution_report("2"))

    assert "artifact_file_hash_mismatch" in _failure_kinds(package_dir)


def test_verify_package_reports_missing_artifact_file(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = write_json(tmp_path / "report.json", execution_report())
    added = add_artifact_to_package(package_dir, report)
    (package_dir / added.artifact_path).unlink()

    assert "artifact_file_missing" in _failure_kinds(package_dir)


def test_verify_package_reports_execution_report_raw_payload_hash_mismatch(
    tmp_path: Path,
) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    raw = package_dir / "artifacts" / "execution" / "raw" / "order.fix"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text("8=FIX.4.4", encoding="utf-8")
    report = write_json(
        tmp_path / "report.json",
        {
            **execution_report(),
            "raw_payload_ref": "artifacts/execution/raw/order.fix",
            "raw_payload_hash": sha256_bytes(raw.read_bytes()),
        },
    )
    add_artifact_to_package(package_dir, report)

    raw.write_text("tampered", encoding="utf-8")

    assert "artifact_raw_payload_hash_mismatch" in _failure_kinds(package_dir)


def test_verify_package_reports_backtest_artifact_ref_missing(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    evidence = write_json(
        tmp_path / "evidence.json",
        backtest_evidence(
            equity_curve={
                "path": "artifacts/backtest/equity_curve.csv",
                "hash": "sha256:" + "2" * 64,
            }
        ),
    )
    add_artifact_to_package(package_dir, evidence)

    assert "artifact_ref_missing" in _failure_kinds(package_dir)


def test_verify_package_reports_backtest_artifact_ref_hash_mismatch(
    tmp_path: Path,
) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    curve = package_dir / "artifacts" / "backtest" / "equity_curve.csv"
    curve.parent.mkdir(parents=True, exist_ok=True)
    curve.write_text("timestamp,equity\n2026-05-14T00:00:00Z,100\n", encoding="utf-8")
    evidence = write_json(
        tmp_path / "evidence.json",
        backtest_evidence(
            equity_curve={
                "path": "artifacts/backtest/equity_curve.csv",
                "hash": sha256_bytes(curve.read_bytes()),
            }
        ),
    )
    add_artifact_to_package(package_dir, evidence)

    curve.write_text("timestamp,equity\n2026-05-14T00:00:00Z,101\n", encoding="utf-8")

    assert "artifact_ref_hash_mismatch" in _failure_kinds(package_dir)


def test_pkg_verify_artifacts_cli_uses_package_verifier(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = write_json(tmp_path / "report.json", execution_report())
    add_artifact_to_package(package_dir, report)

    result = CliRunner().invoke(app, ["pkg", "verify-artifacts", str(package_dir)])

    assert result.exit_code == 0, result.output
    assert '"ok": true' in result.output


def test_qst_verify_package_includes_artifact_checks(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = write_json(tmp_path / "report.json", execution_report())
    added = add_artifact_to_package(package_dir, report)
    write_json(package_dir / added.artifact_path, execution_report("2"))

    result = CliRunner().invoke(app, ["verify", str(package_dir)])

    assert result.exit_code == 1
    assert "artifact_file_hash_mismatch" in result.output
