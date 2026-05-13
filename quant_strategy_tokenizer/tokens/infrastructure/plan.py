"""Plan infrastructure tokens."""

from __future__ import annotations

from quant_strategy_tokenizer.core.output import TokenOutput
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
from quant_strategy_tokenizer.types.plan import NoopPlan, OrderIntentPlan


@token(
    id="plan.noop",
    layer="infrastructure",
    category="plan",
    purity="contextual_read",
    inputs={"decision": "Decision"},
    outputs={"plan": "Plan"},
    contracts=[
        {
            "name": "passthrough_accept",
            "inputs": {"decision": {"kind": "accept", "reason": "test"}},
            "params": {},
            "expected_output": {
                "plan": {"kind": "noop", "decision": {"kind": "accept", "reason": "test"}, "reason": "p0_no_order_intent"}
            },
        },
        {
            "name": "passthrough_reject",
            "inputs": {"decision": {"kind": "reject", "reason": "test"}},
            "params": {},
            "expected_output": {
                "plan": {"kind": "noop", "decision": {"kind": "reject", "reason": "test"}, "reason": "p0_no_order_intent"}
            },
        },
    ],
    description="Pass-through plan node; preserves decision but emits no order intent.",
)
def plan_noop(decision: Decision) -> TokenOutput:
    return TokenOutput(values={"plan": NoopPlan(decision=parse_decision(decision))})


@token(
    id="plan.order_intent",
    layer="infrastructure",
    category="plan",
    purity="contextual_read",
    inputs={"decision": "Decision", "sizing": "Number"},
    outputs={"plan": "Plan"},
    params_schema={
        "side": {"type": "string", "enum": ["long", "short"]},
    },
    contracts=[
        {
            "name": "accept_emits_order_intent",
            "inputs": {"decision": {"kind": "accept", "reason": "entry"}, "sizing": 1.5},
            "params": {"side": "long"},
            "expected_output": {
                "plan": {
                    "kind": "order_intent",
                    "decision": {"kind": "accept", "reason": "entry"},
                    "side": "long",
                    "sizing": 1.5,
                    "reason": "decision accepted; order intent emitted (venue-neutral)",
                }
            },
        },
        {
            "name": "block_emits_blocked_noop",
            "inputs": {
                "decision": {
                    "kind": "block",
                    "reason": "position_cap_exceeded",
                    "severity": "critical",
                },
                "sizing": 1.5,
            },
            "params": {"side": "long"},
            "expected_output": {
                "plan": {
                    "kind": "noop",
                    "decision": {
                        "kind": "block",
                        "reason": "position_cap_exceeded",
                        "severity": "critical",
                    },
                    "reason": "position_cap_exceeded",
                    "blocked": True,
                }
            },
        },
        {
            "name": "unknown_emits_unknown_noop",
            "inputs": {
                "decision": {"kind": "unknown", "missing_info_kind": "dependency_unknown"},
                "sizing": 1.5,
            },
            "params": {"side": "long"},
            "expected_output": {
                "plan": {
                    "kind": "noop",
                    "decision": {"kind": "unknown", "missing_info_kind": "dependency_unknown", "reason": ""},
                    "reason": "dependency_unknown",
                    "unknown": True,
                }
            },
        },
    ],
    description="Emit venue-neutral order intent for accepted decisions, otherwise no-op.",
)
def plan_order_intent(
    decision: Decision,
    sizing: float,
    side: str,
) -> TokenOutput:
    parsed = parse_decision(decision)
    if isinstance(parsed, Accept):
        return TokenOutput(
            values={
                "plan": OrderIntentPlan(
                    decision=parsed,
                    side=side,  # type: ignore[arg-type]
                    sizing=float(sizing),
                )
            }
        )
    if isinstance(parsed, Reject):
        return TokenOutput(values={"plan": NoopPlan(decision=parsed, reason=parsed.reason)})
    if isinstance(parsed, Block):
        return TokenOutput(
            values={"plan": NoopPlan(decision=parsed, reason=parsed.reason, blocked=True)}
        )
    if isinstance(parsed, Unknown):
        return TokenOutput(
            values={
                "plan": NoopPlan(
                    decision=parsed,
                    reason=parsed.missing_info_kind,
                    unknown=True,
                )
            }
        )
    if isinstance(parsed, ErrorDecision):
        return TokenOutput(
            values={"plan": NoopPlan(decision=parsed, reason=parsed.message, error=True)}
        )
    if isinstance(parsed, Abstain):
        return TokenOutput(values={"plan": NoopPlan(decision=parsed, reason=parsed.reason)})
    raise AssertionError(f"Unhandled decision: {parsed!r}")
