"""Decision infrastructure tokens."""

from __future__ import annotations

from typing import Literal

import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import bool_series
from quant_strategy_tokenizer.tokens.registry import token
from quant_strategy_tokenizer.types.decision import (
    Abstain,
    Accept,
    Block,
    Decision,
    ErrorDecision,
    Reject,
    Unknown,
    parse_decision,
)


@token(
    id="decision.lift_bool",
    layer="infrastructure",
    category="decision",
    purity="contextual_read",
    inputs={"series": "TimeSeries[bool]"},
    outputs={"decision": "Decision"},
    params_schema={
        "at": {"type": "string", "enum": ["now"], "default": "now"},
        "accept_reason": {"type": "string", "default": "accepted"},
        "reject_reason": {"type": "string", "default": "rejected"},
    },
    contracts=[
        {
            "name": "last_true_accepts",
            "inputs": {"series": [False, True]},
            "params": {"at": "now", "accept_reason": "cross", "reject_reason": "no_cross"},
            "expected_output": {"decision": {"kind": "accept", "reason": "cross"}},
        },
        {
            "name": "last_false_rejects",
            "inputs": {"series": [True, False]},
            "params": {"at": "now", "accept_reason": "cross", "reject_reason": "no_cross"},
            "expected_output": {"decision": {"kind": "reject", "reason": "no_cross"}},
        },
    ],
    description="Lift the latest boolean series value into a Decision.",
)
def decision_lift_bool(
    series: pd.Series,
    at: Literal["now"] = "now",
    accept_reason: str = "accepted",
    reject_reason: str = "rejected",
) -> TokenOutput:
    del at
    values = bool_series(series)
    if values.empty:
        return TokenOutput(
            values={"decision": Unknown(missing_info_kind="data_unavailable")},
            status="unknown",
            unknown_reason="insufficient_data",
        )
    latest = bool(values.iloc[-1])
    decision: Decision = Accept(reason=accept_reason) if latest else Reject(reason=reject_reason)
    return TokenOutput(values={"decision": decision})


@token(
    id="decision.reduce",
    layer="infrastructure",
    category="decision",
    purity="contextual_read",
    inputs={"decisions": "Decision[]"},
    outputs={"decision": "Decision"},
    params_schema={
        "policy": {"type": "string", "enum": ["all_accept", "any_accept"], "default": "all_accept"},
        "unknown_handling": {
            "type": "string",
            "enum": ["treat_as_reject", "treat_as_unknown", "ignore"],
        },
    },
    contracts=[
        {
            "name": "all_accept_accepts",
            "inputs": {
                "decisions": [
                    {"kind": "accept", "reason": "a"},
                    {"kind": "accept", "reason": "b"},
                ]
            },
            "params": {"policy": "all_accept", "unknown_handling": "treat_as_reject"},
            "expected_output": {"decision": {"kind": "accept", "reason": "all_accept"}},
        },
        {
            "name": "all_accept_rejects",
            "inputs": {
                "decisions": [
                    {"kind": "accept", "reason": "a"},
                    {"kind": "reject", "reason": "b"},
                ]
            },
            "params": {"policy": "all_accept", "unknown_handling": "treat_as_reject"},
            "expected_output": {"decision": {"kind": "reject", "reason": "b"}},
        },
    ],
    description="Reduce a list of Decisions into one final Decision.",
)
def decision_reduce(
    decisions: list[Decision],
    policy: Literal["all_accept", "any_accept"] = "all_accept",
    unknown_handling: Literal["treat_as_reject", "treat_as_unknown", "ignore"] = "treat_as_reject",
) -> TokenOutput:
    parsed = [parse_decision(decision) for decision in decisions]
    if not parsed:
        return TokenOutput(values={"decision": Unknown(missing_info_kind="dependency_unknown")}, status="unknown", unknown_reason="empty_decisions")

    unsupported = [item for item in parsed if isinstance(item, Block | Abstain)]
    if unsupported:
        first = unsupported[0]
        return TokenOutput(
            values={
                "decision": ErrorDecision(
                    exception_kind="unsupported_decision_variant",
                    message=f"decision.reduce/v1 cannot consume {first.kind}",
                )
            },
            status="error",
            error_kind="unsupported_decision_variant",
        )

    errors = [item for item in parsed if item.kind == "error"]
    if errors:
        first_error = errors[0]
        if isinstance(first_error, ErrorDecision):
            return TokenOutput(
                values={"decision": first_error},
                status="error",
                error_kind=first_error.exception_kind,
            )

    unknowns = [item for item in parsed if item.kind == "unknown"]
    usable = [item for item in parsed if item.kind != "unknown" or unknown_handling == "ignore"]

    if unknowns and unknown_handling == "treat_as_unknown":
        return TokenOutput(values={"decision": Unknown(missing_info_kind="dependency_unknown")})

    if unknowns and unknown_handling == "treat_as_reject":
        return TokenOutput(values={"decision": Reject(reason="unknown_treated_as_reject")})

    if policy == "any_accept":
        for item in usable:
            if item.kind == "accept":
                return TokenOutput(values={"decision": Accept(reason="any_accept")})
        first_reject = next((item for item in usable if item.kind == "reject"), None)
        reason = first_reject.reason if isinstance(first_reject, Reject) else "none_accept"
        return TokenOutput(values={"decision": Reject(reason=reason)})

    for item in usable:
        if item.kind == "reject" and isinstance(item, Reject):
            return TokenOutput(values={"decision": Reject(reason=item.reason)})
    all_accept = all(item.kind == "accept" for item in usable)
    if all_accept:
        return TokenOutput(values={"decision": Accept(reason="all_accept")})
    return TokenOutput(values={"decision": Reject(reason="not_all_accept")})


def _decision_from_kind(
    kind: str,
    *,
    reason: str,
    severity: str = "critical",
) -> Decision:
    if kind == "accept":
        return Accept(reason=reason)
    if kind == "reject":
        return Reject(reason=reason)
    if kind == "block":
        if severity not in {"warning", "critical", "fatal"}:
            severity = "critical"
        return Block(reason=reason, severity=severity)  # type: ignore[arg-type]
    if kind == "abstain":
        return Abstain(reason=reason)
    if kind == "unknown":
        return Unknown(missing_info_kind="dependency_unknown", reason=reason)
    if kind == "error":
        return ErrorDecision(exception_kind="mapped_decision", message=reason)
    raise ValueError(f"Unsupported target kind: {kind}")


@token(
    id="decision.map_status",
    layer="infrastructure",
    category="decision",
    purity="contextual_read",
    inputs={"decision": "Decision"},
    outputs={"decision": "Decision"},
    params_schema={
        "mapping": {"type": "object", "default": {}},
        "reason": {"type": "string", "default": "mapped"},
        "severity": {"type": "string", "enum": ["warning", "critical", "fatal"], "default": "critical"},
    },
    contracts=[
        {
            "name": "preserves_unmapped_accept",
            "inputs": {"decision": {"kind": "accept", "reason": "entry"}},
            "params": {"mapping": {}, "reason": "mapped"},
            "expected_output": {"decision": {"kind": "accept", "reason": "entry"}},
        },
        {
            "name": "maps_reject_to_abstain",
            "inputs": {"decision": {"kind": "reject", "reason": "no_signal"}},
            "params": {"mapping": {"reject": "abstain"}, "reason": "rule_not_applicable"},
            "expected_output": {"decision": {"kind": "abstain", "reason": "rule_not_applicable"}},
        },
    ],
    description="Map a Decision status to another Decision status by explicit kind mapping.",
)
def decision_map_status(
    decision: Decision,
    mapping: dict[str, str] | None = None,
    reason: str = "mapped",
    severity: str = "critical",
) -> TokenOutput:
    parsed = parse_decision(decision)
    target = (mapping or {}).get(parsed.kind)
    if target is None:
        return TokenOutput(values={"decision": parsed})
    return TokenOutput(values={"decision": _decision_from_kind(target, reason=reason, severity=severity)})


def _demote_blocks(
    decisions: list[Decision],
    block_handling: str,
) -> TokenOutput | list[Decision]:
    demoted: list[Decision] = []
    for decision in decisions:
        if not isinstance(decision, Block):
            demoted.append(decision)
            continue
        if block_handling == "forward":
            demoted.append(decision)
        elif block_handling == "treat_as_reject":
            demoted.append(Reject(reason=f"block_demoted: {decision.reason}"))
        elif block_handling == "treat_as_error":
            error = ErrorDecision(
                exception_kind="block_treated_as_error",
                message=f"decision.reduce: {decision.reason}",
            )
            return TokenOutput(values={"decision": error}, status="error", error_kind=error.exception_kind)
        else:
            raise ValueError(f"Unsupported block_handling: {block_handling}")
    return demoted


def _demote_abstains(
    decisions: list[Decision],
    abstain_handling: str,
) -> TokenOutput | tuple[list[Decision], bool]:
    demoted: list[Decision] = []
    skipped = False
    for decision in decisions:
        if not isinstance(decision, Abstain):
            demoted.append(decision)
            continue
        if abstain_handling == "skip":
            skipped = True
        elif abstain_handling == "treat_as_reject":
            demoted.append(Reject(reason=f"abstain: {decision.reason}"))
        elif abstain_handling == "treat_as_accept":
            demoted.append(Accept(reason=f"abstain_accepted: {decision.reason}"))
        elif abstain_handling == "error":
            error = ErrorDecision(
                exception_kind="abstain_treated_as_error",
                message=f"decision.reduce: {decision.reason}",
            )
            return TokenOutput(values={"decision": error}, status="error", error_kind=error.exception_kind)
        else:
            raise ValueError(f"Unsupported abstain_handling: {abstain_handling}")
    return demoted, skipped


def _highest_severity(blocks: list[Block]) -> str:
    order = {"warning": 0, "critical": 1, "fatal": 2}
    return max(blocks, key=lambda block: order[block.severity]).severity


def _merged_evidence(blocks: list[Block]) -> dict[str, object]:
    merged: dict[str, object] = {}
    for block in blocks:
        merged.update(block.evidence)
    return merged


@token(
    id="decision.reduce",
    version=2,
    behavior_version=1,
    layer="infrastructure",
    category="decision",
    purity="contextual_read",
    inputs={"decisions": "Decision[]"},
    outputs={"decision": "Decision"},
    params_schema={
        "policy": {"type": "string", "enum": ["all_accept", "any_accept"], "default": "all_accept"},
        "unknown_handling": {
            "type": "string",
            "enum": ["treat_as_reject", "treat_as_unknown", "ignore", "error"],
            "default": "treat_as_reject",
        },
        "block_handling": {
            "type": "string",
            "enum": ["forward", "treat_as_reject", "treat_as_error"],
            "default": "forward",
        },
        "abstain_handling": {
            "type": "string",
            "enum": ["skip", "treat_as_reject", "treat_as_accept", "error"],
            "default": "skip",
        },
    },
    contracts=[
        {
            "name": "block_forward_default",
            "inputs": {
                "decisions": [
                    {"kind": "accept", "reason": "a"},
                    {"kind": "block", "reason": "cap", "severity": "critical"},
                ]
            },
            "params": {"policy": "all_accept", "unknown_handling": "treat_as_reject"},
            "expected_output": {"decision": {"kind": "block", "reason": "cap", "severity": "critical"}},
        },
        {
            "name": "abstain_skip_with_accept",
            "inputs": {
                "decisions": [
                    {"kind": "accept", "reason": "a"},
                    {"kind": "abstain", "reason": "not_applicable"},
                ]
            },
            "params": {"policy": "all_accept", "unknown_handling": "treat_as_reject"},
            "expected_output": {"decision": {"kind": "accept", "reason": "all_accept"}},
        },
        {
            "name": "block_demoted_to_reject",
            "inputs": {
                "decisions": [
                    {"kind": "accept", "reason": "a"},
                    {"kind": "block", "reason": "cap", "severity": "critical"},
                ]
            },
            "params": {
                "policy": "all_accept",
                "unknown_handling": "treat_as_reject",
                "block_handling": "treat_as_reject",
            },
            "expected_output": {"decision": {"kind": "reject", "reason": "block_demoted: cap"}},
        },
    ],
    description="Reduce Decisions with P1 Block and Abstain priority semantics.",
)
def decision_reduce_v2(
    decisions: list[Decision],
    policy: Literal["all_accept", "any_accept"] = "all_accept",
    unknown_handling: Literal[
        "treat_as_reject",
        "treat_as_unknown",
        "ignore",
        "error",
    ] = "treat_as_reject",
    block_handling: Literal["forward", "treat_as_reject", "treat_as_error"] = "forward",
    abstain_handling: Literal[
        "skip",
        "treat_as_reject",
        "treat_as_accept",
        "error",
    ] = "skip",
) -> TokenOutput:
    parsed = [parse_decision(decision) for decision in decisions]
    if not parsed:
        return TokenOutput(values={"decision": Unknown(missing_info_kind="dependency_unknown")}, status="unknown", unknown_reason="empty_decisions")

    errors = [item for item in parsed if isinstance(item, ErrorDecision)]
    if errors:
        first = errors[0]
        error = ErrorDecision(
            exception_kind=first.exception_kind,
            message=f"decision.reduce: {first.message}",
            source_node=first.source_node,
        )
        return TokenOutput(values={"decision": error}, status="error", error_kind=error.exception_kind)

    block_result = _demote_blocks(parsed, block_handling)
    if isinstance(block_result, TokenOutput):
        return block_result
    abstain_result = _demote_abstains(block_result, abstain_handling)
    if isinstance(abstain_result, TokenOutput):
        return abstain_result
    usable, skipped_abstain = abstain_result

    blocks = [item for item in usable if isinstance(item, Block)]
    if blocks:
        chosen = blocks[0]
        return TokenOutput(
            values={
                "decision": Block(
                    reason=chosen.reason,
                    severity=_highest_severity(blocks),  # type: ignore[arg-type]
                    evidence=_merged_evidence(blocks),
                )
            }
        )

    unknowns = [item for item in usable if isinstance(item, Unknown)]
    usable_without_unknown = [item for item in usable if not isinstance(item, Unknown)]
    if unknowns and unknown_handling == "treat_as_unknown":
        return TokenOutput(values={"decision": Unknown(missing_info_kind="dependency_unknown")})
    if unknowns and unknown_handling == "treat_as_reject":
        usable_without_unknown.append(Reject(reason="unknown_treated_as_reject"))
    if unknowns and unknown_handling == "error":
        error = ErrorDecision(
            exception_kind="unknown_treated_as_error",
            message="decision.reduce: unknown dependency",
        )
        return TokenOutput(values={"decision": error}, status="error", error_kind=error.exception_kind)

    if not usable_without_unknown and skipped_abstain:
        return TokenOutput(
            values={
                "decision": Unknown(
                    missing_info_kind="dependency_unknown",
                    reason="all_abstain",
                )
            },
            status="unknown",
            unknown_reason="all_abstain",
        )

    if policy == "any_accept":
        for item in usable_without_unknown:
            if isinstance(item, Accept):
                return TokenOutput(values={"decision": Accept(reason="any_accept")})
        first_reject = next((item for item in usable_without_unknown if isinstance(item, Reject)), None)
        return TokenOutput(
            values={"decision": Reject(reason=first_reject.reason if first_reject else "none_accept")}
        )

    for item in usable_without_unknown:
        if isinstance(item, Reject):
            return TokenOutput(values={"decision": Reject(reason=item.reason)})
    if usable_without_unknown and all(isinstance(item, Accept) for item in usable_without_unknown):
        return TokenOutput(values={"decision": Accept(reason="all_accept")})
    return TokenOutput(values={"decision": Reject(reason="not_all_accept")})
