from __future__ import annotations

import copy
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
MANIFEST = ROOT / "tests" / "coverage_cases" / "custom_token_governance" / "custom_token_routes.yaml"


def _matrix() -> dict[str, Any]:
    return validator.load_matrix(MATRIX)


def _rows_by_id(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in matrix["patterns"]}


def _custom_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in matrix["patterns"]
        if row["expected_classification"] == "custom_token_required"
    ]


def test_custom_token_route_manifest_covers_all_active_custom_rows() -> None:
    matrix = _matrix()
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "qst-custom-token-governance/0.1"
    routes = {route["pattern_id"]: route for route in manifest["routes"]}
    custom_ids = {row["id"] for row in _custom_rows(matrix)}
    assert custom_ids <= set(routes)

    for row in _custom_rows(matrix):
        governance = routes[row["id"]]
        matrix_route = row["custom_token_route"]
        assert governance["input_ports"] == matrix_route["input_ports"]
        assert governance["output_ports"] == matrix_route["output_ports"]
        assert governance["remain_custom_route"] is True
        assert governance["execution_boundary"] == "not_approved_not_granted_not_executed"


def test_net_normalize_stale_custom_route_is_retired() -> None:
    row = _rows_by_id(_matrix())["int_040_net_normalize"]

    assert row["expected_classification"] == "supported"
    assert "custom_token_route" not in row
    assert row["evidence"]["required_tokens"] == ["weight.normalize_net"]
    assert row["false_supported"]["mechanical_status"] == "pass"
    assert row["gaps"] == {"missing_tokens": [], "missing_types": [], "kernel_gaps": []}

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    stale_ids = {review["pattern_id"] for review in manifest["stale_route_reviews"]}
    assert "int_040_net_normalize" in stale_ids


def test_validator_fails_custom_row_without_governance_manifest_entry() -> None:
    matrix = copy.deepcopy(_matrix())
    row = _rows_by_id(matrix)["int_040_net_normalize"]
    row["expected_classification"] = "custom_token_required"
    row["coverage"] = {
        "direct_builtin_possible": False,
        "partial_record_possible": False,
        "custom_token_possible": True,
        "reserved": False,
        "non_goal": False,
    }
    row["custom_token_route"] = {
        "reason": "Synthetic missing governance route.",
        "input_ports": ["weights"],
        "output_ports": ["weights"],
    }

    issues, _summary = validator.validate_matrix(matrix, repo_root=ROOT)
    assert "custom_route_governance_missing" in {issue.code for issue in issues}


def test_report_exposes_custom_token_governance_and_cap_status() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]
    governance = report["custom_token_governance"]
    markdown = coverage_report.render_markdown({"coverage_frontier": report})

    assert governance["active_route_count"] == 10
    assert governance["missing_governance_rows"] == []
    assert governance["stale_route_count"] == 0
    assert governance["route_cap"] == 0.4
    assert report["metrics"]["custom_token_route_share"] < governance["route_cap"]
    assert "Custom Token Governance" in markdown
    assert "int_013_kdj_cross_basic" in markdown
    assert "int_040_net_normalize" in markdown


def test_custom_runtime_boundary_is_not_weakened_by_governance() -> None:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    policy = manifest["policy"]

    assert policy["verification_boundary"] == "metadata_and_integrity_only"
    assert policy["approval_boundary"] == "explicit_local_approval_required"
    assert policy["grant_boundary"] == "short_lived_execution_grant_required"
    assert policy["execution_boundary"] == "not_approved_not_granted_not_executed"
    assert "approve" not in {route.get("route_class") for route in manifest["routes"]}
