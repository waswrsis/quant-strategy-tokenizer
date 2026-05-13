"""Plan infrastructure tokens."""

from __future__ import annotations

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens.registry import token
from quant_strategy_tokenizer.types.decision import Decision, parse_decision
from quant_strategy_tokenizer.types.plan import NoopPlan


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
