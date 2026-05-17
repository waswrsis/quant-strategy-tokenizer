from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PANEL_FACTOR_WEIGHT_DIR = ROOT / "tests" / "coverage_cases" / "panel_factor_weight"
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import report_strategy_coverage as coverage_report  # noqa: E402
import validate_strategy_coverage_matrix as validator  # noqa: E402

MATRIX = ROOT / "docs" / "reports" / "strategy_coverage_matrix.yaml"
PR8_CASES = {
    "beta_neutral_signal": PANEL_FACTOR_WEIGHT_DIR / "beta_neutral_signal.partial.gkr.yaml",
    "equal_rank_market_neutral_weights": (
        PANEL_FACTOR_WEIGHT_DIR / "equal_rank_market_neutral_weights.partial.gkr.yaml"
    ),
    "group_neutral_net_normalize_weights": (
        PANEL_FACTOR_WEIGHT_DIR / "group_neutral_net_normalize_weights.partial.gkr.yaml"
    ),
    "inverse_vol_weight": PANEL_FACTOR_WEIGHT_DIR / "inverse_vol_weight.partial.gkr.yaml",
    "sector_neutral_rank": PANEL_FACTOR_WEIGHT_DIR / "sector_neutral_rank.partial.gkr.yaml",
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


def test_pr8_candidate_gkrs_validate_hash_and_canonicalize(tmp_path: Path) -> None:
    for case_id, strategy in PR8_CASES.items():
        rel_strategy = str(strategy.relative_to(ROOT))
        _run_cli("validate", rel_strategy)

        actual_hashes = json.loads(_run_cli("hash", rel_strategy).stdout)
        expected_hashes = json.loads(
            (PANEL_FACTOR_WEIGHT_DIR / f"{case_id}.hashes.json").read_text(encoding="utf-8")
        )
        assert actual_hashes == expected_hashes

        canonical_output = tmp_path / f"{case_id}.canonical.json"
        _run_cli("canonicalize", rel_strategy, "--output", str(canonical_output))
        assert json.loads(canonical_output.read_text(encoding="utf-8"))["strategy"]["id"]


def test_pr8_matrix_counts_are_registered() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]

    assert report["pattern_count"] == 115
    assert report["benchmark_groups"]["internal_matrix"]["count"] == 90
    assert report["benchmark_groups"]["external_benchmark"]["count"] == 20
    assert report["benchmark_groups"]["dogfood"]["count"] == 5
    assert report["check"]["result"] == "pass"


def test_pr8_updated_rows_have_expected_evidence_and_boundaries() -> None:
    rows = _rows_by_id(_matrix())

    inverse_vol = rows["int_041_inverse_vol_weight"]
    assert inverse_vol["expected_classification"] == "supported"
    assert inverse_vol["evidence"]["required_tokens"] == ["weight.inverse_vol_weight"]
    assert inverse_vol["evidence"]["examples"] == [
        "tests/coverage_cases/panel_factor_weight/inverse_vol_weight.partial.gkr.yaml"
    ]
    assert inverse_vol["gaps"]["kernel_gaps"] == []
    assert "custom_token_route" not in inverse_vol

    sector_neutral = rows["int_049_sector_neutral_rank"]
    assert sector_neutral["expected_classification"] == "supported"
    assert sector_neutral["evidence"]["required_tokens"] == [
        "factor.sector_neutral_rank",
        "selection.top_k",
    ]
    assert sector_neutral["gaps"]["missing_types"] == []
    assert sector_neutral["gaps"]["kernel_gaps"] == []
    assert "explicit group metadata" in " ".join(sector_neutral["boundary"]["limitations"])

    beta_neutral = rows["int_050_beta_neutral_signal"]
    assert beta_neutral["expected_classification"] == "supported"
    assert beta_neutral["evidence"]["required_tokens"] == [
        "factor.beta_neutral_signal",
        "decision.signal_to_decision",
    ]
    assert beta_neutral["gaps"] == {"missing_tokens": [], "missing_types": [], "kernel_gaps": []}
    assert "not full beta-neutral portfolio" in " ".join(beta_neutral["boundary"]["limitations"])


def test_pr8_report_includes_panel_factor_weight_batch_summary() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]
    markdown = coverage_report.render_markdown({"coverage_frontier": report})

    assert report["panel_factor_weight_batch"]["count"] == 8
    assert "Panel / Factor / Weight Batch" in markdown
    assert "int_041_inverse_vol_weight" in markdown
    assert "int_049_sector_neutral_rank" in markdown
    assert "int_050_beta_neutral_signal" in markdown
