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
MANIFEST = ROOT / "tests" / "coverage_cases" / "reserved_non_goal_boundaries" / "boundary_cases.yaml"


def _matrix() -> dict[str, Any]:
    return validator.load_matrix(MATRIX)


def _manifest() -> dict[str, Any]:
    loaded = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _boundary_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in matrix["patterns"]
        if row["expected_classification"] in {"reserved", "non_goal"}
    ]


def _rows_by_id(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in matrix["patterns"]}


def test_boundary_manifest_covers_all_reserved_and_non_goal_rows() -> None:
    matrix = _matrix()
    manifest = _manifest()
    cases = {case["pattern_id"]: case for case in manifest["cases"]}
    boundary_ids = {row["id"] for row in _boundary_rows(matrix)}

    assert manifest["schema_version"] == "qst-reserved-non-goal-boundary/0.1"
    assert boundary_ids <= set(cases)

    for row in _boundary_rows(matrix):
        case = cases[row["id"]]
        assert case["classification"] == row["expected_classification"]
        assert case["diagnostic_class"]
        assert case["boundary_class"]
        assert "supported" in case["must_not_reclassify_as"]


def test_reserved_rows_have_future_design_or_deferral_boundary() -> None:
    matrix = _matrix()
    manifest = _manifest()
    cases = {case["pattern_id"]: case for case in manifest["cases"]}
    rows = _rows_by_id(matrix)

    expected_diagnostics = {
        "reserved_event_stream_required",
        "order_book_event_runtime_not_supported",
        "reserved_hft_runtime_required",
        "reserved_distribution_required",
        "optimizer_solver_contract_required",
    }
    actual_diagnostics = {
        case["diagnostic_class"]
        for case in cases.values()
        if case["classification"] == "reserved"
    }
    assert expected_diagnostics <= actual_diagnostics

    for row in _boundary_rows(matrix):
        if row["expected_classification"] != "reserved":
            continue
        case = cases[row["id"]]
        assert row["boundary"]["reserved_reason"]
        assert case["future_stage_allowed"] is True
        assert case["preferred_future_stage"] != "non_goal"

    assert rows["int_072_event_join_asof"]["expected_classification"] == "reserved"
    assert rows["int_079_order_book_imbalance"]["expected_classification"] == "reserved"
    assert rows["int_080_hft_latency_arbitrage"]["expected_classification"] == "reserved"
    assert rows["int_074_distribution_normal_fit"]["expected_classification"] == "reserved"
    assert rows["ext_020_portfolio_optimizer"]["expected_classification"] == "reserved"


def test_non_goal_rows_are_out_of_scope_and_not_custom_routes() -> None:
    matrix = _matrix()
    manifest = _manifest()
    cases = {case["pattern_id"]: case for case in manifest["cases"]}
    negative = {case["id"]: case for case in manifest["negative_tests"]}

    for row in _boundary_rows(matrix):
        if row["expected_classification"] != "non_goal":
            continue
        case = cases[row["id"]]
        assert row["boundary"]["non_goal_reason"]
        assert case["future_stage_allowed"] is False
        assert "partially_supported" in case["must_not_reclassify_as"]
        assert "custom_token_required" in case["must_not_reclassify_as"]
        assert "custom_token_route" not in row

    assert negative["live_broker_execution"]["expected_classification"] == "non_goal"
    assert negative["exchange_order_router"]["diagnostic_class"] == "exchange_routing_non_goal"
    assert negative["full_backtest_engine_request"]["diagnostic_class"] == "full_backtest_engine_non_goal"


def test_validator_fails_reserved_row_without_boundary_manifest_entry() -> None:
    matrix = copy.deepcopy(_matrix())
    for row in matrix["patterns"]:
        if row["expected_classification"] == "reserved":
            row["id"] = "synthetic_reserved_without_manifest"
            break

    issues, _summary = validator.validate_matrix(matrix, repo_root=ROOT)
    assert "reserved_non_goal_boundary_case_missing" in {issue.code for issue in issues}


def test_validator_fails_non_goal_row_with_wrong_future_stage_policy() -> None:
    matrix = copy.deepcopy(_matrix())
    manifest = copy.deepcopy(_manifest())
    non_goal_id = next(
        row["id"]
        for row in matrix["patterns"]
        if row["expected_classification"] == "non_goal"
    )
    for case in manifest["cases"]:
        if case["pattern_id"] == non_goal_id:
            case["future_stage_allowed"] = True
            break

    boundary_cases = validator._reserved_non_goal_boundary_cases(manifest)
    row = _rows_by_id(matrix)[non_goal_id]
    issues = []

    def add(code: str, path: str, message: str, severity: str = "error") -> None:
        issues.append(validator.MatrixIssue(severity, code, path, message))

    validator._validate_reserved_non_goal_boundary(
        row,
        f"patterns[{non_goal_id}]",
        "non_goal",
        boundary_cases,
        add,
    )
    assert "non_goal_boundary_future_stage_allowed" in {issue.code for issue in issues}


def test_report_includes_reserved_non_goal_boundary_section() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]
    boundary = report["reserved_non_goal_boundary"]
    markdown = coverage_report.render_markdown({"coverage_frontier": report})

    assert boundary["reserved_count"] == 12
    assert boundary["non_goal_count"] == 5
    assert boundary["missing_boundary_rows"] == []
    assert boundary["status"] == "pass"
    assert "Reserved / Non-Goal Boundary" in markdown
    assert "int_072_event_join_asof" in markdown
    assert "ext_017_live_broker_execution" in markdown
