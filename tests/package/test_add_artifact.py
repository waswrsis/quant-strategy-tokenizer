from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quant_strategy_tokenizer.cli import app
from quant_strategy_tokenizer.package import (
    add_artifact_to_package,
    package_strategy,
    read_package,
)
from tests.package._artifact_helpers import (
    backtest_evidence,
    execution_report,
    portfolio_snapshot,
    write_json,
)

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "uses_ewm_with_provenance.qst.yaml"


def _tracked_hash(package_dir: Path, path: str) -> str:
    manifest = read_package(package_dir).manifest
    for entry in manifest.files:
        if entry.path == path:
            return entry.sha256
    raise AssertionError(f"{path} not tracked")


def test_add_artifact_updates_manifest_sections(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = write_json(tmp_path / "report.json", execution_report())
    snapshot = write_json(tmp_path / "snapshot.json", portfolio_snapshot())
    evidence = write_json(tmp_path / "evidence.json", backtest_evidence())

    report_result = add_artifact_to_package(package_dir, report)
    snapshot_result = add_artifact_to_package(package_dir, snapshot)
    evidence_result = add_artifact_to_package(package_dir, evidence)
    manifest = read_package(package_dir).manifest

    assert manifest.artifacts is not None
    assert report_result.artifact_path == "artifacts/execution/reports/report.json"
    assert snapshot_result.artifact_path == "artifacts/portfolio/snapshots/snapshot.json"
    assert evidence_result.artifact_path == "artifacts/backtest/backtest_evidence.json"
    assert report_result.artifact_path in manifest.artifacts.execution.reports
    assert snapshot_result.artifact_path in manifest.artifacts.portfolio.snapshots
    assert evidence_result.artifact_path == manifest.artifacts.backtest.evidence
    assert (package_dir / report_result.artifact_path).exists()
    assert (package_dir / snapshot_result.artifact_path).exists()
    assert (package_dir / evidence_result.artifact_path).exists()


def test_add_artifact_overwrites_same_path_idempotently(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = tmp_path / "report.json"
    dest = "artifacts/execution/reports/execution.json"

    write_json(report, execution_report("1"))
    add_artifact_to_package(package_dir, report, dest_path=dest)
    first_hash = _tracked_hash(package_dir, dest)

    write_json(report, execution_report("2"))
    add_artifact_to_package(package_dir, report, dest_path=dest)
    second_hash = _tracked_hash(package_dir, dest)
    manifest = read_package(package_dir).manifest

    assert first_hash != second_hash
    assert manifest.artifacts is not None
    assert manifest.artifacts.execution.reports.count(dest) == 1
    assert [entry.path for entry in manifest.files].count(dest) == 1


def test_add_artifact_rejects_unknown_artifact_version(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    bad = write_json(tmp_path / "bad.json", {"artifact_version": "unknown/1"})

    with pytest.raises(ValueError, match="Unsupported artifact_version"):
        add_artifact_to_package(package_dir, bad)


@pytest.mark.parametrize("bad_dest", ["../report.json", "/report.json", "artifacts\\report.json"])
def test_add_artifact_rejects_unsafe_dest_path(tmp_path: Path, bad_dest: str) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = write_json(tmp_path / "report.json", execution_report())

    with pytest.raises(ValueError):
        add_artifact_to_package(package_dir, report, dest_path=bad_dest)


def test_pkg_add_artifact_cli_outputs_summary(tmp_path: Path) -> None:
    package_dir = tmp_path / "uses_ewm.qstpkg"
    package_strategy(STRATEGY, package_dir)
    report = write_json(tmp_path / "report.json", execution_report())

    result = CliRunner().invoke(app, ["pkg", "add-artifact", str(package_dir), str(report)])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["artifact_path"] == "artifacts/execution/reports/report.json"
    assert payload["artifact_version"] == "qst-execution-report/1"
