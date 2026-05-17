from __future__ import annotations

import json
import subprocess
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


def _report() -> dict[str, Any]:
    return coverage_report.build_report(validator.load_matrix(MATRIX), repo_root=ROOT)


def test_report_json_includes_expected_counts() -> None:
    report = _report()["coverage_frontier"]

    assert report["pattern_count"] == 105
    assert report["benchmark_groups"]["internal_matrix"]["count"] == 80
    assert report["benchmark_groups"]["external_benchmark"]["count"] == 20
    assert report["benchmark_groups"]["dogfood"]["count"] == 5
    assert report["dogfood_pattern_count"] == 5
    assert report["dogfood_target"]["publication_status"] == "pass"
    assert report["check"]["result"] == "pass"


def test_check_passes_current_matrix() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "report_strategy_coverage.py"),
            str(MATRIX),
            "--check",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "check: pass" in completed.stdout


def test_json_cli_output_is_parseable() -> None:
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
    assert payload["coverage_frontier"]["pattern_count"] == 105
    assert payload["coverage_frontier"]["check"]["result"] == "pass"


def test_markdown_writer_creates_expected_sections(tmp_path: Path) -> None:
    output = tmp_path / "strategy_coverage_report.md"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "report_strategy_coverage.py"),
            str(MATRIX),
            "--markdown",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    text = output.read_text(encoding="utf-8")
    assert "# Strategy Coverage Report" in text
    assert "## Benchmark Groups" in text
    assert "## Metrics" in text
    assert "## Next Best Expansions" in text
    assert "direct_builtin_coverage" in text
