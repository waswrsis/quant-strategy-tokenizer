from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import validate_strategy_coverage_matrix as validator  # noqa: E402

MATRIX = ROOT / "docs" / "reports" / "strategy_coverage_matrix.yaml"


def _matrix() -> dict[str, Any]:
    return validator.load_matrix(MATRIX)


def _issue_codes(matrix: dict[str, Any]) -> set[str]:
    issues, _summary = validator.validate_matrix(matrix, repo_root=ROOT)
    return {issue.code for issue in issues}


def _first_row(matrix: dict[str, Any], classification: str) -> dict[str, Any]:
    for row in matrix["patterns"]:
        if row["expected_classification"] == classification:
            return row
    raise AssertionError(f"missing row for {classification}")


def test_current_matrix_validator_passes() -> None:
    issues, summary = validator.validate_matrix(_matrix(), repo_root=ROOT)

    assert issues == []
    assert summary["pattern_count"] == 115
    assert summary["benchmark_groups"]["internal_matrix"] == 90
    assert summary["benchmark_groups"]["external_benchmark"] == 20
    assert summary["benchmark_groups"]["dogfood"] == 5


def test_duplicate_id_fails() -> None:
    matrix = copy.deepcopy(_matrix())
    matrix["patterns"][1]["id"] = matrix["patterns"][0]["id"]

    assert "duplicate_pattern_id" in _issue_codes(matrix)


def test_invalid_classification_fails() -> None:
    matrix = copy.deepcopy(_matrix())
    matrix["patterns"][0]["expected_classification"] = "maybe_supported"

    assert "invalid_classification" in _issue_codes(matrix)


def test_custom_route_missing_reason_or_ports_fails() -> None:
    matrix = copy.deepcopy(_matrix())
    row = _first_row(matrix, "custom_token_required")
    row["custom_token_route"] = {"reason": "", "input_ports": [], "output_ports": []}

    codes = _issue_codes(matrix)
    assert "custom_route_missing_reason" in codes
    assert "custom_route_missing_input_ports" in codes
    assert "custom_route_missing_output_ports" in codes


def test_reserved_row_missing_reserved_reason_fails() -> None:
    matrix = copy.deepcopy(_matrix())
    row = _first_row(matrix, "reserved")
    row["boundary"]["reserved_reason"] = None

    assert "reserved_missing_reserved_reason" in _issue_codes(matrix)


def test_non_goal_row_missing_non_goal_reason_fails() -> None:
    matrix = copy.deepcopy(_matrix())
    row = _first_row(matrix, "non_goal")
    row["boundary"]["non_goal_reason"] = None

    assert "non_goal_missing_non_goal_reason" in _issue_codes(matrix)


def test_external_source_anchor_missing_fails() -> None:
    matrix = copy.deepcopy(_matrix())
    for row in matrix["patterns"]:
        if row["benchmark_group"] == "external_benchmark":
            row["market_weight"]["evidence"] = [
                "docs/reports/external_benchmark_sources.md#src-does-not-exist"
            ]
            break

    assert "external_source_anchor_missing" in _issue_codes(matrix)
