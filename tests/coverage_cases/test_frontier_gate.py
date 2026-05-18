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
CI = ROOT / ".github" / "workflows" / "ci.yml"
PUBLIC_STATEMENT = ROOT / "docs" / "reports" / "strategy_coverage_public_statement.md"


def _matrix() -> dict[str, Any]:
    return validator.load_matrix(MATRIX)


def _report() -> dict[str, Any]:
    return coverage_report.build_report(_matrix(), repo_root=ROOT)["coverage_frontier"]


def test_frontier_gate_passes_with_publication_thresholds() -> None:
    report = _report()
    gate = report["frontier_gate"]

    assert gate["result"] == "pass"
    assert gate["headline"]["metric"] == "routable_record_coverage_raw"
    assert gate["headline"]["value"] == report["metrics"]["routable_record_coverage_raw"]
    assert gate["threshold_policy"]["custom_token_route_max"] == 0.30
    assert gate["threshold_policy"]["false_supported_max"] == 0.02
    assert gate["threshold_policy"]["reserved_non_goal_false_positive_max"] == 0.02
    assert gate["threshold_policy"]["direct_builtin_min"] == "measured_frontier"
    assert gate["threshold_policy"]["routable_record_min"] == "measured_frontier"
    assert gate["issues"] == []


def test_frontier_gate_json_cli_exposes_headline_and_group_split() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "report_strategy_coverage.py"),
            str(MATRIX),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    gate = payload["coverage_frontier"]["frontier_gate"]
    assert gate["result"] == "pass"
    assert gate["headline"]["metric"] == "routable_record_coverage_raw"
    assert gate["headline"]["percent"] == 89.7
    assert gate["group_split"]["internal_matrix"]["count"] == 95
    assert gate["group_split"]["external_benchmark"]["count"] == 20
    assert gate["group_split"]["dogfood"]["count"] == 5


def test_frontier_gate_markdown_and_public_statement_match() -> None:
    report = _report()
    markdown = coverage_report.render_markdown({"coverage_frontier": report})
    statement = PUBLIC_STATEMENT.read_text(encoding="utf-8")

    assert "## Frontier Gate" in markdown
    assert "## Public Statement" in markdown
    assert "routable_record_coverage_raw" in markdown
    assert "89.70%" in markdown
    assert "89.70%" in statement
    assert "Direct built-in coverage" in statement
    assert "Discounted routable record coverage" in statement
    assert "does not include runtime, backtest, broker, exchange, HFT" in statement.replace("\n", " ")


def test_coverage_validation_job_runs_frontier_gate_commands() -> None:
    workflow = yaml.safe_load(CI.read_text(encoding="utf-8"))
    coverage_job = workflow["jobs"]["coverage-validation"]
    commands = [
        step["run"]
        for step in coverage_job["steps"]
        if isinstance(step, dict) and isinstance(step.get("run"), str)
    ]

    assert "python tools/validate_strategy_coverage_matrix.py docs/reports/strategy_coverage_matrix.yaml" in commands
    assert "python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --check" in commands
    assert "python tools/report_strategy_coverage.py docs/reports/strategy_coverage_matrix.yaml --json" in commands
    assert "python -m pytest tests/coverage_cases -q" in commands
