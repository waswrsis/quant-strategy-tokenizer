"""P0 Decision discriminated union."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Never

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class Accept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["accept"] = "accept"
    reason: str
    evidence: dict[str, Any] = {}
    source_node: str | None = None


class Reject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["reject"] = "reject"
    reason: str
    evidence: dict[str, Any] = {}
    source_node: str | None = None


class Unknown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["unknown"] = "unknown"
    missing_info_kind: Literal["data_unavailable", "warmup", "dependency_unknown"] = "dependency_unknown"
    evidence: dict[str, Any] = {}
    source_node: str | None = None


class ErrorDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["error"] = "error"
    exception_kind: str
    message: str
    source_node: str | None = None


Decision = Annotated[Accept | Reject | Unknown | ErrorDecision, Field(discriminator="kind")]
decision_adapter: TypeAdapter[Decision] = TypeAdapter(Decision)


def parse_decision(value: object) -> Decision:
    """Validate a Python object as a P0 Decision."""

    return decision_adapter.validate_python(value)


def decision_to_dict(value: Decision) -> dict[str, Any]:
    """Serialize a Decision to a plain dict."""

    return value.model_dump(mode="json", exclude_none=True)


def assert_never(value: Never) -> Never:
    """Exhaustiveness helper for explicit Decision branching."""

    raise AssertionError(f"Unhandled value: {value!r}")
