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

EXPECTED_DOGFOOD_IDS = {
    "dog_001_original_multi_asset_mean_reversion_grid",
    "dog_002_single_asset_trend_following_fsm",
    "dog_003_cross_sectional_factor_panel",
    "dog_004_custom_ml_score_signal",
    "dog_005_reserved_event_stream_orderbook",
}
CANDIDATES = {
    "dog_001_original_multi_asset_mean_reversion_grid": DOGFOOD_DIR
    / "original_multi_asset_mean_reversion_grid.partial.gkr.yaml",
    "dog_002_single_asset_trend_following_fsm": DOGFOOD_DIR
    / "single_asset_trend_following_fsm.partial.gkr.yaml",
    "dog_003_cross_sectional_factor_panel": DOGFOOD_DIR / "cross_sectional_factor_panel.partial.gkr.yaml",
}
INTENTS = {
    "dog_001_original_multi_asset_mean_reversion_grid": DOGFOOD_DIR
    / "original_multi_asset_mean_reversion_grid.intent.yaml",
    "dog_002_single_asset_trend_following_fsm": DOGFOOD_DIR
    / "single_asset_trend_following_fsm.intent.yaml",
    "dog_003_cross_sectional_factor_panel": DOGFOOD_DIR / "cross_sectional_factor_panel.intent.yaml",
    "dog_004_custom_ml_score_signal": DOGFOOD_DIR / "custom_ml_score_signal.intent.yaml",
    "dog_005_reserved_event_stream_orderbook": DOGFOOD_DIR / "reserved_event_stream_orderbook.intent.yaml",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def _matrix() -> dict[str, Any]:
    return validator.load_matrix(MATRIX)


def _dogfood_rows() -> dict[str, dict[str, Any]]:
    rows = {
        row["id"]: row
        for row in _matrix()["patterns"]
        if row.get("benchmark_group") == "dogfood"
    }
    return rows


def _intent(case_id: str) -> dict[str, Any]:
    return _load_yaml(INTENTS[case_id])["dogfood_case"]


def test_dogfood_target_rows_are_complete() -> None:
    rows = _dogfood_rows()

    assert set(rows) == EXPECTED_DOGFOOD_IDS
    assert len(rows) == 5
    assert rows["dog_002_single_asset_trend_following_fsm"]["expected_classification"] == "partially_supported"
    assert rows["dog_003_cross_sectional_factor_panel"]["expected_classification"] == "partially_supported"
    assert rows["dog_004_custom_ml_score_signal"]["expected_classification"] == "custom_token_required"
    assert rows["dog_005_reserved_event_stream_orderbook"]["expected_classification"] == "reserved"


def test_dogfood_intents_have_required_gap_records() -> None:
    for case_id in EXPECTED_DOGFOOD_IDS:
        case = _intent(case_id)
        assert case["id"] == case_id
        assert case["expected_classification"] == case["verdict"]["classification"]
        assert "required_tokens" in case
        assert "missing_tokens" in case
        assert "missing_types" in case
        assert "kernel_gaps" in case

    custom = _intent("dog_004_custom_ml_score_signal")
    route = custom["custom_token_route"]
    assert route["reason"]
    assert route["input_ports"]
    assert route["output_ports"]

    reserved = _intent("dog_005_reserved_event_stream_orderbook")
    assert "EventStream" in reserved["missing_types"]
    assert "OrderBook" in reserved["missing_types"]
    assert reserved["candidate_gkr"]["status"] == "not_attempted_reserved_design"


def test_candidate_dogfood_gkrs_validate_hash_and_canonicalize(tmp_path: Path) -> None:
    for case_id, candidate in CANDIDATES.items():
        rel_candidate = str(candidate.relative_to(ROOT))
        subprocess.run(
            [sys.executable, "-m", "qst.cli", "validate", rel_candidate],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        completed = subprocess.run(
            [sys.executable, "-m", "qst.cli", "hash", rel_candidate],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        actual = json.loads(completed.stdout)
        expected = _intent(case_id)["validation_evidence"]["hash"]
        assert actual["graph_hash"] == expected["graph_hash"]
        assert actual["param_hash"] == expected["param_hash"]
        assert actual["instance_hash"] == expected["instance_hash"]

        output = tmp_path / f"{case_id}.canonical.json"
        subprocess.run(
            [sys.executable, "-m", "qst.cli", "canonicalize", rel_candidate, "--output", str(output)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(output.read_text(encoding="utf-8"))["strategy"]["id"]


def test_matrix_rows_encode_custom_and_reserved_boundaries() -> None:
    rows = _dogfood_rows()

    custom = rows["dog_004_custom_ml_score_signal"]
    assert custom["custom_token_route"]["reason"]
    assert custom["custom_token_route"]["input_ports"]
    assert custom["custom_token_route"]["output_ports"]
    assert custom["dogfood_evidence"]["candidate_gkr"] is None

    reserved = rows["dog_005_reserved_event_stream_orderbook"]
    assert reserved["boundary"]["reserved_reason"]
    assert "EventStream" in reserved["gaps"]["missing_types"]
    assert "OrderBook" in reserved["gaps"]["missing_types"]
    assert reserved["dogfood_evidence"]["candidate_gkr"] is None


def test_report_json_and_markdown_include_dogfood_target_set() -> None:
    report = coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]

    assert report["dogfood_pattern_count"] == 5
    assert report["dogfood_target"]["mvp_status"] == "pass"
    assert report["dogfood_target"]["publication_status"] == "pass"
    assert {row["id"] for row in report["dogfood"]["rows"]} == EXPECTED_DOGFOOD_IDS

    markdown = coverage_report.render_markdown({"coverage_frontier": report})
    assert "Publication target" in markdown
    for case_id in EXPECTED_DOGFOOD_IDS:
        assert case_id in markdown
