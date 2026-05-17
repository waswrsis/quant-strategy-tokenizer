from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import report_strategy_coverage as coverage_report  # noqa: E402
import validate_strategy_coverage_matrix as validator  # noqa: E402

MATRIX = ROOT / "docs" / "reports" / "strategy_coverage_matrix.yaml"
DOGFOOD_DIR = ROOT / "tests" / "coverage_cases" / "dogfood"
INTENT = DOGFOOD_DIR / "original_multi_asset_mean_reversion_grid.intent.yaml"
CANDIDATE = DOGFOOD_DIR / "original_multi_asset_mean_reversion_grid.partial.gkr.yaml"
REPORT = ROOT / "docs" / "reports" / "original_failure_strategy_dogfood.md"


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _coverage_report() -> dict[str, Any]:
    matrix = validator.load_matrix(MATRIX)
    return coverage_report.build_report(matrix, repo_root=ROOT)["coverage_frontier"]


def test_dogfood_intent_fixture_has_required_fields() -> None:
    data = _load_yaml(INTENT)
    case = data["dogfood_case"]

    assert case["id"] == "dog_001_original_multi_asset_mean_reversion_grid"
    assert case["expected_classification"] == "partially_supported"
    assert case["candidate_gkr"]["path"] == str(CANDIDATE.relative_to(ROOT)).replace("\\", "/")
    assert "panel.zscore" in case["required_tokens"]
    assert "grid recipe" in case["missing_tokens"]
    assert "Instrument metadata" in case["missing_types"]
    assert case["kernel_gaps"]
    assert case["verdict"]["classification"] == "partially_supported"


def test_candidate_partial_gkr_validates() -> None:
    subprocess.run(
        [sys.executable, "-m", "qst.cli", "validate", str(CANDIDATE.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_candidate_hashes_match_intent_fixture() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "qst.cli", "hash", str(CANDIDATE.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    actual = json.loads(completed.stdout)
    expected = _load_yaml(INTENT)["dogfood_case"]["validation_evidence"]["hash"]

    assert actual["graph_hash"] == expected["graph_hash"]
    assert actual["param_hash"] == expected["param_hash"]
    assert actual["instance_hash"] == expected["instance_hash"]


def test_candidate_canonicalizes_to_local_artifact(tmp_path: Path) -> None:
    output = tmp_path / "dogfood.canonical.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "qst.cli",
            "canonicalize",
            str(CANDIDATE.relative_to(ROOT)),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["strategy"]["id"] == "original_multi_asset_mean_reversion_grid_partial"


def test_dogfood_report_records_evidence_and_boundaries() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "dog_001_original_multi_asset_mean_reversion_grid" in text
    assert "partially_supported" in text
    assert str(CANDIDATE.relative_to(ROOT)).replace("\\", "/") in text
    assert "VWAP add optimizer" in text
    assert "broker/exchange" in text


def test_coverage_matrix_dogfood_row_is_pr4_evidence() -> None:
    matrix = validator.load_matrix(MATRIX)
    rows = [
        row for row in matrix["patterns"] if row["id"] == "dog_001_original_multi_asset_mean_reversion_grid"
    ]
    assert len(rows) == 1
    row = rows[0]

    assert row["benchmark_group"] == "dogfood"
    assert row["expected_classification"] == "partially_supported"
    assert row["false_supported"]["mechanical_status"] == "pass"
    assert row["false_supported"]["semantic_status"] == "pending"
    assert row["false_supported"]["boundary_status"] == "pass"
    assert row["dogfood_evidence"]["candidate_gkr"] == str(CANDIDATE.relative_to(ROOT)).replace("\\", "/")
    assert row["gaps"]["missing_tokens"]
    assert row["gaps"]["missing_types"]
    assert row["gaps"]["kernel_gaps"]


def test_report_json_and_markdown_include_dogfood_details() -> None:
    report = _coverage_report()
    dogfood = report["dogfood"]
    candidate_path = str(CANDIDATE.relative_to(ROOT)).replace("\\", "/")

    assert dogfood["rows"][0]["id"] == "dog_001_original_multi_asset_mean_reversion_grid"
    assert dogfood["rows"][0]["classification"] == "partially_supported"
    assert dogfood["rows"][0]["candidate_gkr"] == candidate_path

    markdown = coverage_report.render_markdown({"coverage_frontier": report})
    assert "dog_001_original_multi_asset_mean_reversion_grid" in markdown
    assert candidate_path in markdown


def test_report_cli_json_includes_dogfood_candidate_path() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "report_strategy_coverage.py"), str(MATRIX), "--json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    rows = payload["coverage_frontier"]["dogfood"]["rows"]
    assert rows[0]["candidate_gkr"] == str(CANDIDATE.relative_to(ROOT)).replace("\\", "/")
