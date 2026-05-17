from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import report_strategy_coverage as coverage_report  # noqa: E402
import validate_strategy_coverage_matrix as validator  # noqa: E402

MATRIX = ROOT / "docs" / "reports" / "strategy_coverage_matrix.yaml"
KERNEL_REVIEW = ROOT / "docs" / "reports" / "kernel_gap_review.md"


def _matrix() -> dict[str, Any]:
    return validator.load_matrix(MATRIX)


def _rows_by_id(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in matrix["patterns"]}


def _active_kernel_gap_categories(matrix: dict[str, Any]) -> set[str]:
    categories: set[str] = set()
    for row in matrix["patterns"]:
        if row.get("benchmark_group") == "dogfood":
            continue
        for gap in row.get("gaps", {}).get("kernel_gaps", []) or []:
            categories.add(gap["category"])
    return categories


def test_kernel_gap_review_covers_active_gap_categories() -> None:
    matrix = _matrix()
    text = KERNEL_REVIEW.read_text(encoding="utf-8")

    assert "# Kernel Gap Review" in text
    for category in _active_kernel_gap_categories(matrix):
        assert f"`{category}`" in text
    assert "int_050_beta_neutral_signal" in text
    assert "EventStream" in text
    assert "Distribution" in text
    assert "optimizer solver" in text


def test_beta_neutral_row_retires_stale_numeric_gap() -> None:
    row = _rows_by_id(_matrix())["int_050_beta_neutral_signal"]

    assert row["expected_classification"] == "supported"
    assert row["coverage"]["direct_builtin_possible"] is True
    assert "custom_token_route" not in row
    assert row["evidence"]["required_tokens"] == ["factor.beta_neutral_signal", "decision.signal_to_decision"]
    assert row["evidence"]["examples"] == [
        "tests/coverage_cases/panel_factor_weight/beta_neutral_signal.partial.gkr.yaml"
    ]
    assert row["gaps"]["missing_tokens"] == []
    assert row["gaps"]["kernel_gaps"] == []
    assert "portfolio construction" in " ".join(row["boundary"]["limitations"])


def test_remaining_numeric_determinism_gaps_are_distribution_or_solver_deferrals() -> None:
    matrix = _matrix()
    numeric_rows = []
    for row in matrix["patterns"]:
        for gap in row.get("gaps", {}).get("kernel_gaps", []) or []:
            if gap["category"] == "numeric_determinism_gap":
                numeric_rows.append((row, gap))

    assert {row["id"] for row, _gap in numeric_rows} == {
        "int_071_optimizer_mean_variance",
        "int_074_distribution_normal_fit",
        "int_075_distribution_quantile",
        "ext_019_distribution_var",
        "ext_020_portfolio_optimizer",
    }
    for row, gap in numeric_rows:
        combined = " ".join(
            [
                row["description"],
                gap["description"],
                row["boundary"].get("reserved_reason") or "",
            ]
        )
        assert "Distribution" in combined or "solver" in combined


def test_pr7_matrix_counts_are_stable() -> None:
    matrix = _matrix()
    report = coverage_report.build_report(matrix, repo_root=ROOT)["coverage_frontier"]

    assert report["pattern_count"] == 115
    assert report["benchmark_groups"]["internal_matrix"]["count"] == 90
    assert report["benchmark_groups"]["external_benchmark"]["count"] == 20
    assert report["benchmark_groups"]["dogfood"]["count"] == 5
    assert report["metrics"]["kernel_gap_count"] == 18
    assert report["check"]["result"] == "pass"
