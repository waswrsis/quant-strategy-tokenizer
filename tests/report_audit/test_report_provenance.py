from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from qst.report_audit import (
    FinancialReportProvenance,
    ReportSectionEvidence,
    ReportSourceRecord,
    ReportToolInvocation,
    review_financial_report,
    seal_report_provenance,
)

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
NOW = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)


def _report(**updates: object) -> FinancialReportProvenance:
    values: dict[str, object] = {
        "run_id": "finrobot-run-42",
        "recorded_at": NOW,
        "agent_name": "FinRobot Analyst",
        "agent_role": "financial analyst",
        "task_summary": "Review ACME annual report",
        "model_id": "declared-model",
        "model_version": "2026-07",
        "prompt_ref": "prompt:financial-review-v1",
        "expected_ticker": "ACME",
        "expected_report_period": "FY2025",
        "sources": (
            ReportSourceRecord(
                source_ref="filing:acme:2025",
                status="verified",
                ticker="ACME",
                report_period="FY2025",
                url="https://example.test/acme-2025",
                artifact_id=HASH_A,
            ),
        ),
        "tool_invocations": (
            ReportToolInvocation(
                tool_name="filing_reader",
                normalized_parameters={"ticker": "ACME", "period": "FY2025"},
                status="success",
                input_artifact_ids=(HASH_A,),
                output_artifact_ids=(HASH_B,),
                output_paths=("reports/acme.md",),
            ),
        ),
        "report_sections": (
            ReportSectionEvidence(section_id="valuation", evidence_ids=(HASH_A,)),
        ),
        "output_artifact_ids": (HASH_B,),
        "valuation_assumptions": {"discount_rate": 0.1},
        "draft_for_human_review": True,
    }
    values.update(updates)
    return seal_report_provenance(FinancialReportProvenance.model_validate(values))


def test_complete_report_provenance_is_ready_for_human_review(tmp_path: Path) -> None:
    decision = review_financial_report(_report(), workspace_root=tmp_path)
    assert decision.ready_for_human_review
    assert decision.issue_codes == ()


def test_review_gates_failed_sources_paths_retries_and_unsupported_sections(
    tmp_path: Path,
) -> None:
    report = _report(
        sources=(ReportSourceRecord(source_ref="missing", status="failed"),),
        tool_invocations=(
            ReportToolInvocation(
                tool_name="fallback_reader",
                normalized_parameters={},
                status="failed",
                output_paths=(str(tmp_path.parent / "outside.md"),),
                retry_count=1,
                fallback_used=True,
                truncated=True,
            ),
        ),
        report_sections=(ReportSectionEvidence(section_id="valuation", evidence_ids=()),),
        changed_assumptions=("discount_rate",),
        assumption_change_reasons={},
    )
    decision = review_financial_report(report, workspace_root=tmp_path)
    assert not decision.ready_for_human_review
    assert {
        "QST_REPORT_SOURCE_MISSING_OR_FAILED",
        "QST_REPORT_OUTPUT_OUTSIDE_WORKSPACE",
        "QST_REPORT_TOOL_FAILED",
        "QST_REPORT_TOOL_RETRY_OR_FALLBACK",
        "QST_REPORT_TOOL_OUTPUT_TRUNCATED",
        "QST_REPORT_SECTION_WITHOUT_EVIDENCE",
        "QST_REPORT_VALUATION_CHANGE_WITHOUT_REASON",
    }.issubset(decision.issue_codes)


def test_report_tool_parameters_reject_embedded_credentials() -> None:
    with pytest.raises(ValidationError, match="secret-bearing"):
        ReportToolInvocation(
            tool_name="unsafe_tool",
            normalized_parameters={"api_key": "redacted"},
            status="success",
        )
    valid = ReportToolInvocation(
        tool_name="token_inspector",
        normalized_parameters={"token_ref": "core.math.add/v1/bv1"},
        status="success",
    )
    assert valid.normalized_parameters["token_ref"] == "core.math.add/v1/bv1"
