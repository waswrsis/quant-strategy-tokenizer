from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CORE_RULE_DIR = ROOT / "tests" / "coverage_cases" / "core_rule"
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import report_strategy_coverage as coverage_report  # noqa: E402
import validate_strategy_coverage_matrix as validator  # noqa: E402

MATRIX = ROOT / "docs" / "reports" / "strategy_coverage_matrix.yaml"
CORE_RULE_CASES = {
    "macd_trend": CORE_RULE_DIR / "macd_trend.partial.gkr.yaml",
    "atr_filter": CORE_RULE_DIR / "atr_filter.partial.gkr.yaml",
    "linear_regression_slope": CORE_RULE_DIR / "linear_regression_slope.partial.gkr.yaml",
    "beta_residual_timeseries": CORE_RULE_DIR / "beta_residual_timeseries.partial.gkr.yaml",
    "long_short_decision": CORE_RULE_DIR / "long_short_decision.partial.gkr.yaml",
}


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "qst.cli", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _matrix() -> dict[str, Any]:
    return validator.load_matrix(MATRIX)


def test_pr6_candidate_gkrs_validate_hash_and_canonicalize(tmp_path: Path) -> None:
    for case_id, strategy in CORE_RULE_CASES.items():
        rel_strategy = str(strategy.relative_to(ROOT))
        _run_cli("validate", rel_strategy)

        actual_hashes = json.loads(_run_cli("hash", rel_strategy).stdout)
        expected_hashes = json.loads(
            (CORE_RULE_DIR / f"{case_id}.hashes.json").read_text(encoding="utf-8")
        )
        assert actual_hashes == expected_hashes

        canonical_output = tmp_path / f"{case_id}.canonical.json"
        _run_cli("canonicalize", rel_strategy, "--output", str(canonical_output))
        assert json.loads(canonical_output.read_text(encoding="utf-8"))["strategy"]["id"]


def test_pr6_matrix_counts_and_core_rule_rows_are_registered() -> None:
    matrix = _matrix()
    report = coverage_report.build_report(matrix, repo_root=ROOT)["coverage_frontier"]

    assert report["pattern_count"] == 115
    assert report["benchmark_groups"]["internal_matrix"]["count"] == 90
    assert report["benchmark_groups"]["external_benchmark"]["count"] == 20
    assert report["benchmark_groups"]["dogfood"]["count"] == 5

    rows = {row["id"]: row for row in matrix["patterns"]}
    for row_id in {
        "int_020_macd_trend",
        "int_021_atr_filter",
        "int_022_linear_regression_slope",
    }:
        assert rows[row_id]["expected_classification"] == "supported"
        assert rows[row_id]["coverage"]["direct_builtin_possible"] is True
        assert rows[row_id]["false_supported"]["mechanical_status"] == "pass"

    assert rows["int_013_kdj_cross_basic"]["expected_classification"] == "custom_token_required"
    assert rows["int_014_kdj_with_ema_filter"]["expected_classification"] == "custom_token_required"


def test_pr6_report_includes_core_rule_expansion_summary() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]
    markdown = coverage_report.render_markdown({"coverage_frontier": report})

    assert "pattern_count" in json.dumps(report, sort_keys=True)
    assert "Core rule token batch" in markdown
    assert "int_020_macd_trend" in markdown
    assert "int_021_atr_filter" in markdown
    assert "int_022_linear_regression_slope" in markdown
