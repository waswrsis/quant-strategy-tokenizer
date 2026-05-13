"""Plan value types."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from .decision import Decision, parse_decision


class NoopPlan(BaseModel):
    """No-op plan. It carries the final decision but emits no order intent."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["noop"] = "noop"
    decision: Decision
    reason: str = "p0_no_order_intent"
    blocked: bool | None = None
    unknown: bool | None = None
    error: bool | None = None


class OrderIntentPlan(BaseModel):
    """Venue-neutral order intent emitted after an accepted decision."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["order_intent"] = "order_intent"
    decision: Decision
    side: Literal["long", "short"]
    sizing: float
    reason: str = "decision accepted; order intent emitted (venue-neutral)"


Plan = Annotated[NoopPlan | OrderIntentPlan, Field(discriminator="kind")]
plan_adapter: TypeAdapter[Plan] = TypeAdapter(Plan)


def parse_plan(value: object) -> Plan:
    """Validate a Python object as a plan."""

    if isinstance(value, NoopPlan | OrderIntentPlan):
        return value
    if not isinstance(value, dict):
        raise TypeError(f"Plan must be a dict or plan model, got {type(value).__name__}")
    raw: dict[str, Any] = dict(value)
    if "decision" in raw:
        raw["decision"] = parse_decision(raw["decision"])
    return plan_adapter.validate_python(raw)
