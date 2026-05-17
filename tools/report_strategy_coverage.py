from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_strategy_coverage_matrix import (
    load_matrix,
    validate_matrix,
    validation_payload,
)


@dataclass(frozen=True)
class CheckIssue:
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def build_report(matrix: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    validation_issues, validation_summary = validate_matrix(matrix, repo_root=repo_root)
    patterns = [row for row in matrix.get("patterns", []) if isinstance(row, dict)]
    frontier_patterns = [
        row
        for row in patterns
        if row.get("benchmark_group") != "dogfood" and row.get("status", "active") == "active"
    ]
    dogfood_patterns = [row for row in patterns if row.get("benchmark_group") == "dogfood"]

    total_weight = _weight_sum(frontier_patterns)
    supported = _by_class(frontier_patterns, "supported")
    partial = _by_class(frontier_patterns, "partially_supported")
    custom = _by_class(frontier_patterns, "custom_token_required")
    mechanically_reviewed_supported = [
        row
        for row in supported
        if _false_supported(row).get("mechanical_status") == "pass"
    ]

    custom_discount = _custom_discount(matrix)
    direct_weight = _weight_sum(mechanically_reviewed_supported)
    supported_weight = _weight_sum(supported)
    partial_weight = _weight_sum(partial)
    custom_weight = _weight_sum(custom)
    routable_raw_weight = supported_weight + partial_weight + custom_weight
    routable_discounted_weight = supported_weight + partial_weight + (custom_weight * custom_discount)
    routable_denominator = max(routable_raw_weight, 1)
    supported_denominator = max(len(supported), 1)

    benchmark_groups = _benchmark_group_summary(patterns)
    by_classification = _classification_summary(patterns)
    kernel_gaps = _kernel_gap_records(patterns)
    missing_tokens = _missing_token_records(frontier_patterns)

    metrics = {
        "direct_builtin_coverage": _ratio(direct_weight, total_weight),
        "routable_record_coverage_raw": _ratio(routable_raw_weight, total_weight),
        "routable_record_coverage_discounted": _ratio(routable_discounted_weight, total_weight),
        "custom_token_route_share": _ratio(custom_weight, routable_denominator),
        "false_supported_rate_mechanical": _status_rate(supported, "mechanical_status", "fail", supported_denominator),
        "false_supported_rate_semantic": _status_rate(supported, "semantic_status", "fail", supported_denominator),
        "false_supported_rate_boundary": _status_rate(supported, "boundary_status", "fail", supported_denominator),
        "boundary_false_supported_count": _status_count(supported, "boundary_status", "fail"),
        "kernel_gap_count": len(kernel_gaps),
        "token_bloat_index": _ratio(len({record["name"] for record in missing_tokens}), len(frontier_patterns)),
    }

    report = {
        "coverage_frontier": {
            "schema_version": matrix.get("schema_version"),
            "pattern_count": len(patterns),
            "frontier_pattern_count": len(frontier_patterns),
            "dogfood_pattern_count": len(dogfood_patterns),
            "total_weight": total_weight,
            "benchmark_groups": benchmark_groups,
            "by_classification": by_classification,
            "metrics": metrics,
            "dogfood": _dogfood_summary(dogfood_patterns),
            "next_best_expansions": _next_best_expansions(missing_tokens, kernel_gaps),
            "validation": validation_payload(validation_issues, validation_summary)[
                "strategy_coverage_matrix_validation"
            ],
        }
    }
    check_issues = check_report(report, matrix)
    report["coverage_frontier"]["check"] = {
        "result": "pass" if not check_issues else "fail",
        "issue_count": len(check_issues),
        "issues": [issue.as_dict() for issue in check_issues],
    }
    return report


def check_report(report: dict[str, Any], matrix: dict[str, Any]) -> list[CheckIssue]:
    frontier = report["coverage_frontier"]
    metrics = frontier["metrics"]
    thresholds = matrix.get("thresholds", {}) if isinstance(matrix.get("thresholds"), dict) else {}
    issues: list[CheckIssue] = []

    validation = frontier["validation"]
    if validation["result"] != "pass":
        issues.append(CheckIssue("validator_failed", "coverage matrix validator returned errors"))
    custom_max = _number(thresholds.get("custom_token_route_max"), 1.0)
    if metrics["custom_token_route_share"] > custom_max:
        issues.append(CheckIssue("custom_token_share_exceeds_cap", "custom token route share exceeds cap"))
    false_max = _number(thresholds.get("false_supported_max"), 1.0)
    if metrics["false_supported_rate_mechanical"] > false_max:
        issues.append(
            CheckIssue("mechanical_false_supported_exceeds_cap", "mechanical false-supported rate exceeds cap")
        )
    if metrics["boundary_false_supported_count"] > 0:
        issues.append(CheckIssue("boundary_false_supported_present", "boundary false-supported count is non-zero"))
    groups = frontier["benchmark_groups"]
    external_count = groups.get("external_benchmark", {}).get("count", 0)
    if external_count < 20:
        issues.append(CheckIssue("external_benchmark_count_below_threshold", "external benchmark count is below 20"))
    if frontier["dogfood_pattern_count"] < 1:
        issues.append(CheckIssue("dogfood_missing", "dogfood row is missing"))
    return issues


def render_markdown(report: dict[str, Any]) -> str:
    frontier = report["coverage_frontier"]
    metrics = frontier["metrics"]
    lines = [
        "# Strategy Coverage Report",
        "",
        "Generated from `docs/reports/strategy_coverage_matrix.yaml`.",
        "",
        "This report measures the QST strategy record layer only. It does not claim broker,",
        "exchange, live execution, HFT runtime, full backtest engine, production execution,",
        "profitability, or portfolio optimizer coverage.",
        "",
        "## Summary",
        "",
        f"- Pattern count: `{frontier['pattern_count']}`",
        f"- Frontier pattern count: `{frontier['frontier_pattern_count']}`",
        f"- Dogfood pattern count: `{frontier['dogfood_pattern_count']}`",
        f"- Total frontier weight: `{frontier['total_weight']}`",
        f"- Check result: `{frontier['check']['result']}`",
        "",
        "## Benchmark Groups",
        "",
        "| Group | Count | Weight | Supported | Partial | Custom | Reserved | Non-goal |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for group, summary in frontier["benchmark_groups"].items():
        class_counts = summary["class_counts"]
        lines.append(
            "| {group} | {count} | {weight} | {supported} | {partial} | {custom} | {reserved} | {non_goal} |".format(
                group=group,
                count=summary["count"],
                weight=summary["weight"],
                supported=class_counts.get("supported", 0),
                partial=class_counts.get("partially_supported", 0),
                custom=class_counts.get("custom_token_required", 0),
                reserved=class_counts.get("reserved", 0),
                non_goal=class_counts.get("non_goal", 0),
            )
        )
    lines.extend(
        [
            "",
            "## Classification Summary",
            "",
            "| Classification | Count | Weight |",
            "| --- | ---: | ---: |",
        ]
    )
    for classification, summary in frontier["by_classification"].items():
        lines.append(f"| {classification} | {summary['count']} | {summary['weight']} |")

    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    for key, value in metrics.items():
        lines.append(f"| {key} | {_format_metric(value)} |")

    lines.extend(
        [
            "",
            "## Next Best Expansions",
            "",
            "| Family or kernel | Type | Weighted gain | Complexity cost | Coverage efficiency |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for expansion in frontier["next_best_expansions"]:
        lines.append(
            "| {family_or_kernel} | {type} | {weighted_gain} | {complexity_cost} | {coverage_efficiency} |".format(
                **expansion
            )
        )

    lines.extend(
        [
            "",
            "## Dogfood",
            "",
            f"- Status: `{frontier['dogfood']['status']}`",
            f"- Classifications: `{', '.join(frontier['dogfood']['classifications'])}`",
            "",
            "| Row | Status | Classification | Candidate GKR | Evidence report | Limitations |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in frontier["dogfood"]["rows"]:
        limitations = "; ".join(row["limitations"]) if row["limitations"] else "none"
        lines.append(
            "| {id} | {status} | {classification} | {candidate_gkr} | {report} | {limitations} |".format(
                id=row["id"],
                status=row["status"],
                classification=row["classification"],
                candidate_gkr=row["candidate_gkr"] or "not recorded",
                report=row["report"] or "not recorded",
                limitations=limitations,
            )
        )
    lines.extend(
        [
            "",
            "Dogfood rows remain excluded from headline frontier percentages until the",
            "frontier publication target dogfood set is complete or explicitly deferred.",
            "",
            "## Validation",
            "",
            f"- Validator result: `{frontier['validation']['result']}`",
            f"- Validator issue count: `{frontier['validation']['issue_count']}`",
            f"- Report check result: `{frontier['check']['result']}`",
            f"- Report check issue count: `{frontier['check']['issue_count']}`",
            "",
        ]
    )
    return "\n".join(lines)


def render_text(report: dict[str, Any]) -> str:
    frontier = report["coverage_frontier"]
    metrics = frontier["metrics"]
    return "\n".join(
        [
            "QST strategy coverage report",
            f"patterns: {frontier['pattern_count']}",
            f"frontier_patterns: {frontier['frontier_pattern_count']}",
            f"dogfood_patterns: {frontier['dogfood_pattern_count']}",
            f"check: {frontier['check']['result']}",
            f"direct_builtin_coverage: {_format_metric(metrics['direct_builtin_coverage'])}",
            f"routable_record_coverage_raw: {_format_metric(metrics['routable_record_coverage_raw'])}",
            f"routable_record_coverage_discounted: {_format_metric(metrics['routable_record_coverage_discounted'])}",
            f"custom_token_route_share: {_format_metric(metrics['custom_token_route_share'])}",
            f"kernel_gap_count: {metrics['kernel_gap_count']}",
        ]
    )


def _benchmark_group_summary(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in patterns:
        grouped[str(row.get("benchmark_group", ""))].append(row)
    summary = {}
    for group in sorted(grouped):
        rows = grouped[group]
        class_counts = Counter(str(row.get("expected_classification", "")) for row in rows)
        summary[group] = {
            "count": len(rows),
            "weight": _weight_sum(rows),
            "class_counts": dict(sorted(class_counts.items())),
        }
    return summary


def _classification_summary(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in patterns:
        grouped[str(row.get("expected_classification", ""))].append(row)
    summary = {}
    for classification in sorted(grouped):
        rows = grouped[classification]
        summary[classification] = {"count": len(rows), "weight": _weight_sum(rows)}
    return summary


def _dogfood_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = sorted({str(row.get("status", "")) for row in rows if row.get("status")})
    classifications = sorted({str(row.get("expected_classification", "")) for row in rows})
    return {
        "count": len(rows),
        "status": ", ".join(statuses) if statuses else "missing",
        "classifications": classifications,
        "weight": _weight_sum(rows),
        "rows": [_dogfood_row_summary(row) for row in rows],
    }


def _dogfood_row_summary(row: dict[str, Any]) -> dict[str, Any]:
    evidence = row.get("dogfood_evidence")
    evidence_map = evidence if isinstance(evidence, dict) else {}
    boundary = row.get("boundary")
    boundary_map = boundary if isinstance(boundary, dict) else {}
    limitations = boundary_map.get("limitations")
    return {
        "id": str(row.get("id", "")),
        "status": str(row.get("status", "")),
        "classification": str(row.get("expected_classification", "")),
        "candidate_gkr": _optional_string(evidence_map.get("candidate_gkr")),
        "intent_fixture": _optional_string(evidence_map.get("intent_fixture")),
        "report": _optional_string(evidence_map.get("report")),
        "limitations": [str(item) for item in limitations] if isinstance(limitations, list) else [],
    }


def _missing_token_records(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in patterns:
        gaps = row.get("gaps")
        if not isinstance(gaps, dict):
            continue
        for token in gaps.get("missing_tokens", []) or []:
            if isinstance(token, str) and token:
                records.append({"name": token, "pattern_id": row.get("id"), "weight": _row_weight(row)})
    return records


def _kernel_gap_records(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in patterns:
        gaps = row.get("gaps")
        if not isinstance(gaps, dict):
            continue
        kernel_gaps = gaps.get("kernel_gaps") or []
        if not isinstance(kernel_gaps, list):
            continue
        for gap in kernel_gaps:
            if isinstance(gap, dict) and gap.get("category"):
                records.append(
                    {
                        "name": str(gap["category"]),
                        "pattern_id": row.get("id"),
                        "weight": _row_weight(row),
                    }
                )
    return records


def _next_best_expansions(
    missing_tokens: list[dict[str, Any]],
    kernel_gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aggregate: dict[tuple[str, str], float] = defaultdict(float)
    for record in missing_tokens:
        aggregate[(record["name"], "token")] += float(record["weight"])
    for record in kernel_gaps:
        aggregate[(record["name"], "kernel")] += float(record["weight"])

    expansions = []
    for (name, kind), gain in aggregate.items():
        cost = 1 if kind == "token" else 3
        expansions.append(
            {
                "family_or_kernel": name,
                "type": kind,
                "weighted_gain": _round(gain),
                "complexity_cost": cost,
                "coverage_efficiency": _round(gain / cost),
            }
        )
    return sorted(
        expansions,
        key=lambda item: (
            -float(item["coverage_efficiency"]),
            -float(item["weighted_gain"]),
            str(item["family_or_kernel"]),
        ),
    )[:10]


def _by_class(patterns: list[dict[str, Any]], classification: str) -> list[dict[str, Any]]:
    return [row for row in patterns if row.get("expected_classification") == classification]


def _false_supported(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("false_supported")
    return value if isinstance(value, dict) else {}


def _status_count(rows: list[dict[str, Any]], field: str, value: str) -> int:
    return sum(1 for row in rows if _false_supported(row).get(field) == value)


def _status_rate(rows: list[dict[str, Any]], field: str, value: str, denominator: int) -> float:
    return _round(_status_count(rows, field, value) / denominator)


def _weight_sum(patterns: list[dict[str, Any]]) -> float:
    return _round(sum(_row_weight(row) for row in patterns))


def _row_weight(row: dict[str, Any]) -> float:
    weight = row.get("market_weight")
    if isinstance(weight, dict):
        return _number(weight.get("final"), 0.0)
    return 0.0


def _custom_discount(matrix: dict[str, Any]) -> float:
    policy = matrix.get("coverage_policy")
    if not isinstance(policy, dict):
        return 0.5
    discount = policy.get("custom_token_discount")
    if not isinstance(discount, dict):
        return 0.5
    return _number(discount.get("value"), 0.5)


def _number(value: object, default: float) -> float:
    return float(value) if isinstance(value, int | float) else default


def _optional_string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return _round(numerator / denominator)


def _round(value: float) -> float:
    return round(float(value), 4)


def _format_metric(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report QST strategy coverage metrics.")
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)

    try:
        matrix = load_matrix(args.matrix)
        report = build_report(matrix, repo_root=Path.cwd())
    except Exception as exc:
        print(f"failed to build coverage report: {exc}", file=sys.stderr)
        return 1

    if args.markdown:
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    if args.json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif not args.markdown:
        print(render_text(report))
    else:
        print(f"wrote {args.markdown}")

    if args.check and report["coverage_frontier"]["check"]["result"] != "pass":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
