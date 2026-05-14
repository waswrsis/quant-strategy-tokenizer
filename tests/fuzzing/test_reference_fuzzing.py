from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.composition.fuzzing import (
    check_fuzzing_meets_threshold,
    load_fuzzing_report,
    run_indicator_ewm_fuzzing,
)

REPORT = Path("docs/fuzzing/indicator.ewm.ci_standard.json")


def test_indicator_ewm_fuzzing_is_deterministic() -> None:
    left = run_indicator_ewm_fuzzing(cases=25, seed=1234)
    right = run_indicator_ewm_fuzzing(cases=25, seed=1234)

    assert left == right
    assert left.failed == 0
    assert left.output_digest.startswith("sha256:")


def test_stored_ci_standard_report_reproduces() -> None:
    report = load_fuzzing_report(REPORT)

    assert report.cases == 1000
    assert report.failed == 0
    assert check_fuzzing_meets_threshold(REPORT, "ci_standard")
