from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_GATE_RISK_DIR = ROOT / "tests" / "coverage_cases" / "state_gate_risk"
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import report_strategy_coverage as coverage_report  # noqa: E402
import validate_strategy_coverage_matrix as validator  # noqa: E402

MATRIX = ROOT / "docs" / "reports" / "strategy_coverage_matrix.yaml"
PR9_CASES = {
    "drawdown_volatility_regime": STATE_GATE_RISK_DIR / "drawdown_volatility_regime.partial.gkr.yaml",
    "exposure_turnover_limit_records": (
        STATE_GATE_RISK_DIR / "exposure_turnover_limit_records.partial.gkr.yaml"
    ),
    "min_max_hold_gate": STATE_GATE_RISK_DIR / "min_max_hold_gate.partial.gkr.yaml",
    "rebalance_time_window_records": (
        STATE_GATE_RISK_DIR / "rebalance_time_window_records.partial.gkr.yaml"
    ),
    "stop_take_profit_records": STATE_GATE_RISK_DIR / "stop_take_profit_records.partial.gkr.yaml",
    "trailing_stop_record": STATE_GATE_RISK_DIR / "trailing_stop_record.partial.gkr.yaml",
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


def _rows_by_id(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in matrix["patterns"]}


def test_pr9_candidate_gkrs_validate_hash_and_canonicalize(tmp_path: Path) -> None:
    for case_id, strategy in PR9_CASES.items():
        rel_strategy = str(strategy.relative_to(ROOT))
        _run_cli("validate", rel_strategy)

        actual_hashes = json.loads(_run_cli("hash", rel_strategy).stdout)
        expected_hashes = json.loads(
            (STATE_GATE_RISK_DIR / f"{case_id}.hashes.json").read_text(encoding="utf-8")
        )
        assert actual_hashes == expected_hashes

        canonical_output = tmp_path / f"{case_id}.canonical.json"
        _run_cli("canonicalize", rel_strategy, "--output", str(canonical_output))
        assert json.loads(canonical_output.read_text(encoding="utf-8"))["strategy"]["id"]


def test_pr9_matrix_counts_are_registered() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]

    assert report["pattern_count"] == 120
    assert report["benchmark_groups"]["internal_matrix"]["count"] == 95
    assert report["benchmark_groups"]["external_benchmark"]["count"] == 20
    assert report["benchmark_groups"]["dogfood"]["count"] == 5
    assert report["check"]["result"] == "pass"


def test_pr9_updated_rows_have_expected_evidence_and_boundaries() -> None:
    rows = _rows_by_id(_matrix())

    for row_id, token in {
        "int_027_min_hold_gate": "gate.min_hold",
        "int_028_max_hold_gate": "gate.max_hold",
        "int_029_trailing_stop_record": "risk.trailing_stop_record",
        "int_030_stop_loss_record": "risk.stop_loss_record",
        "int_031_take_profit_record": "risk.take_profit_record",
        "int_035_exposure_cap": "risk.exposure_cap_record",
        "int_055_volatility_regime_gate": "gate.volatility_regime",
    }.items():
        row = rows[row_id]
        assert row["expected_classification"] == "supported"
        assert token in row["evidence"]["required_tokens"]
        assert row["false_supported"]["mechanical_status"] == "pass"
        assert row["gaps"] == {"missing_tokens": [], "missing_types": [], "kernel_gaps": []}

    rebalance = rows["int_032_rebalance_band"]
    assert rebalance["expected_classification"] == "supported"
    assert rebalance["evidence"]["required_tokens"] == ["gate.rebalance", "risk.turnover_limit_record"]
    assert "rebalance scheduler" in " ".join(rebalance["boundary"]["limitations"])

    calendar = rows["int_033_rebalance_calendar"]
    assert calendar["expected_classification"] == "partially_supported"
    assert calendar["gaps"]["missing_types"] == ["Calendar"]
    assert calendar["gaps"]["kernel_gaps"][0]["category"] == "port_temporal_type_gap"

    drawdown = rows["int_056_drawdown_gate"]
    assert drawdown["expected_classification"] == "supported"
    assert drawdown["evidence"]["required_tokens"] == ["gate.drawdown", "risk.max_drawdown_record"]


def test_pr9_report_includes_state_gate_risk_batch_summary() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]
    markdown = coverage_report.render_markdown({"coverage_frontier": report})

    assert report["state_gate_risk_batch"]["count"] == 14
    assert "State / Gate / Risk Batch" in markdown
    assert "int_027_min_hold_gate" in markdown
    assert "int_030_stop_loss_record" in markdown
    assert "int_095_rebalance_exposure_turnover_records" in markdown
