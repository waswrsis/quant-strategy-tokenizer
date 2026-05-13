"""Decision infrastructure tokens."""

from __future__ import annotations

from typing import Literal

import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import bool_series
from quant_strategy_tokenizer.tokens.registry import token
from quant_strategy_tokenizer.types.decision import (
    Accept,
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

    errors = [item for item in parsed if item.kind == "error"]
    if errors:
        first = errors[0]
        if isinstance(first, ErrorDecision):
            return TokenOutput(values={"decision": first}, status="error", error_kind=first.exception_kind)

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
