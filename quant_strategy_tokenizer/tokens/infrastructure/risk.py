"""Risk infrastructure tokens."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens.registry import token
from quant_strategy_tokenizer.types.decision import Accept, Block, Decision, parse_decision


def _passthrough_non_accept(decision: Decision) -> TokenOutput | None:
    parsed = parse_decision(decision)
    if not isinstance(parsed, Accept):
        return TokenOutput(values={"decision": parsed})
    return None


@token(
    id="risk.position_cap",
    layer="infrastructure",
    category="risk",
    purity="contextual_read",
    inputs={"decision": "Decision", "state": "State"},
    outputs={"decision": "Decision"},
    params_schema={
        "max_position": {"type": "number", "minimum": 0},
        "symbol_key": {"type": "string", "default": "current_symbol"},
    },
    contracts=[
        {
            "name": "accept_under_cap_passes",
            "inputs": {
                "decision": {"kind": "accept", "reason": "entry"},
                "state": {"current_symbol": 3},
            },
            "params": {"max_position": 5, "symbol_key": "current_symbol"},
            "expected_output": {"decision": {"kind": "accept", "reason": "entry"}},
        },
        {
            "name": "accept_at_cap_blocks",
            "inputs": {
                "decision": {"kind": "accept", "reason": "entry"},
                "state": {"current_symbol": 5},
            },
            "params": {"max_position": 5, "symbol_key": "current_symbol"},
            "expected_output": {
                "decision": {
                    "kind": "block",
                    "reason": "position_cap_exceeded",
                    "severity": "critical",
                    "evidence": {"current_position": 5.0, "max_position": 5.0},
                }
            },
        },
        {
            "name": "reject_passthrough",
            "inputs": {
                "decision": {"kind": "reject", "reason": "no_signal"},
                "state": {"current_symbol": 5},
            },
            "params": {"max_position": 5, "symbol_key": "current_symbol"},
            "expected_output": {"decision": {"kind": "reject", "reason": "no_signal"}},
        },
    ],
    description="Block accepted decisions when absolute position is at or above cap.",
)
def risk_position_cap(
    decision: Decision,
    state: dict[str, Any],
    max_position: float,
    symbol_key: str = "current_symbol",
) -> TokenOutput:
    passthrough = _passthrough_non_accept(decision)
    if passthrough is not None:
        return passthrough
    current_position = float(state.get(symbol_key, 0))
    if abs(current_position) >= float(max_position):
        return TokenOutput(
            values={
                "decision": Block(
                    reason="position_cap_exceeded",
                    severity="critical",
                    evidence={
                        "current_position": current_position,
                        "max_position": float(max_position),
                    },
                )
            }
        )
    return TokenOutput(values={"decision": parse_decision(decision)})


@token(
    id="risk.notional_cap",
    layer="infrastructure",
    category="risk",
    purity="contextual_read",
    inputs={"decision": "Decision", "state": "State"},
    outputs={"decision": "Decision"},
    params_schema={
        "max_notional": {"type": "number", "minimum": 0},
        "notional_key": {"type": "string", "default": "current_notional"},
    },
    contracts=[
        {
            "name": "accept_under_cap_passes",
            "inputs": {
                "decision": {"kind": "accept", "reason": "entry"},
                "state": {"current_notional": 50},
            },
            "params": {"max_notional": 100, "notional_key": "current_notional"},
            "expected_output": {"decision": {"kind": "accept", "reason": "entry"}},
        },
        {
            "name": "accept_over_cap_blocks",
            "inputs": {
                "decision": {"kind": "accept", "reason": "entry"},
                "state": {"current_notional": 100},
            },
            "params": {"max_notional": 100, "notional_key": "current_notional"},
            "expected_output": {
                "decision": {
                    "kind": "block",
                    "reason": "notional_cap_exceeded",
                    "severity": "critical",
                    "evidence": {"current_notional": 100.0, "max_notional": 100.0},
                }
            },
        },
    ],
    description="Block accepted decisions when absolute notional is at or above cap.",
)
def risk_notional_cap(
    decision: Decision,
    state: dict[str, Any],
    max_notional: float,
    notional_key: str = "current_notional",
) -> TokenOutput:
    passthrough = _passthrough_non_accept(decision)
    if passthrough is not None:
        return passthrough
    current_notional = float(state.get(notional_key, 0))
    if abs(current_notional) >= float(max_notional):
        return TokenOutput(
            values={
                "decision": Block(
                    reason="notional_cap_exceeded",
                    severity="critical",
                    evidence={
                        "current_notional": current_notional,
                        "max_notional": float(max_notional),
                    },
                )
            }
        )
    return TokenOutput(values={"decision": parse_decision(decision)})
