"""P0 plan value types."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from .decision import Decision, parse_decision


class NoopPlan(BaseModel):
    """P0 no-op plan. It carries the final decision but emits no order intent."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["noop"] = "noop"
    decision: Decision
    reason: str = "p0_no_order_intent"


Plan = NoopPlan


def parse_plan(value: object) -> Plan:
    """Validate a Python object as a P0 plan."""

    if isinstance(value, NoopPlan):
        return value
    if not isinstance(value, dict):
        raise TypeError(f"Plan must be a dict or NoopPlan, got {type(value).__name__}")
    raw: dict[str, Any] = dict(value)
    if "decision" in raw:
        raw["decision"] = parse_decision(raw["decision"])
    return NoopPlan.model_validate(raw)
