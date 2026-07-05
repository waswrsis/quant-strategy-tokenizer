"""Deterministic financial-report review gates."""

from __future__ import annotations

from pathlib import Path

from qst.report_audit.models import FinancialReportProvenance, ReportReviewDecision


def review_financial_report(
    report: FinancialReportProvenance, *, workspace_root: Path
) -> ReportReviewDecision:
    issues: list[str] = []
    if report.provenance_id is None:
        issues.append("QST_REPORT_PROVENANCE_UNSEALED")
    if not report.sources or any(
        item.status != "verified" or item.artifact_id is None for item in report.sources
    ):
        issues.append("QST_REPORT_SOURCE_MISSING_OR_FAILED")
    if any(
        (report.expected_ticker and item.ticker != report.expected_ticker)
        or (
            report.expected_report_period
            and item.report_period != report.expected_report_period
        )
        for item in report.sources
        if item.status == "verified"
    ):
        issues.append("QST_REPORT_SOURCE_TICKER_OR_PERIOD_MISMATCH")
    root = workspace_root.resolve()
    if not report.tool_invocations:
        issues.append("QST_REPORT_TOOL_PROVENANCE_REQUIRED")
    for invocation in report.tool_invocations:
        for raw_path in invocation.output_paths:
            path = Path(raw_path)
            candidate = path.resolve() if path.is_absolute() else (root / path).resolve()
            if not candidate.is_relative_to(root):
                issues.append("QST_REPORT_OUTPUT_OUTSIDE_WORKSPACE")
        if invocation.status == "failed":
            issues.append("QST_REPORT_TOOL_FAILED")
        if invocation.retry_count or invocation.fallback_used:
            issues.append("QST_REPORT_TOOL_RETRY_OR_FALLBACK")
        if invocation.truncated:
            issues.append("QST_REPORT_TOOL_OUTPUT_TRUNCATED")
    if not report.report_sections or any(not item.evidence_ids for item in report.report_sections):
        issues.append("QST_REPORT_SECTION_WITHOUT_EVIDENCE")
    if any(
        not report.assumption_change_reasons.get(name, "").strip()
        for name in report.changed_assumptions
    ):
        issues.append("QST_REPORT_VALUATION_CHANGE_WITHOUT_REASON")
    if not report.output_artifact_ids:
        issues.append("QST_REPORT_OUTPUT_ARTIFACT_REQUIRED")
    if not report.draft_for_human_review:
        issues.append("QST_REPORT_MUST_REMAIN_DRAFT_FOR_HUMAN_REVIEW")
    return ReportReviewDecision(
        ready_for_human_review=not issues,
        provenance_id=report.provenance_id,
        issue_codes=tuple(issues),
    )
