"""Structured TypeSpec models for Token System v2."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from quant_strategy_tokenizer.types_v2.value_type import ValueType

TypeKind = Literal[
    "Scalar",
    "TimeSeries",
    "Panel",
    "Decision",
    "Plan",
    "State",
    "Event",
    "EventStream",
]
TypedKind = Literal["Scalar", "TimeSeries", "Panel", "State", "Event", "EventStream"]
AvailableAt = Literal["bar_open", "bar_close", "next_bar_open", "event_time", "unknown"]
Clock = Literal["bar", "event", "none", "unknown"]

_SHORTHAND_RE = re.compile(
    r"^(Scalar|TimeSeries|Panel|State|Event|EventStream)\[([A-Za-z_][A-Za-z0-9_]*)\]$"
)
_BARE_KINDS: set[str] = {"Decision", "Plan"}
_TYPED_KINDS: set[str] = {"Scalar", "TimeSeries", "Panel", "State", "Event", "EventStream"}


class IntrinsicTemporalSpec(BaseModel):
    """Default temporal nature of a type or data source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    default_available_at: AvailableAt = "bar_close"
    default_clock: Clock = "bar"


class TypeSpec(BaseModel):
    """Structured v2 type specification."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: TypeKind
    value_type: ValueType | None = None
    intrinsic_temporal: IntrinsicTemporalSpec | None = None

    @model_validator(mode="before")
    @classmethod
    def _parse_shorthand(cls, value: Any) -> Any:
        if isinstance(value, str):
            if value in _BARE_KINDS:
                return {"kind": value}
            match = _SHORTHAND_RE.fullmatch(value)
            if match is None:
                raise ValueError(f"Unsupported TypeSpec shorthand: {value!r}")
            kind, value_type = match.groups()
            return {"kind": kind, "value_type": value_type}
        return value

    @model_validator(mode="after")
    def _check_value_type(self) -> TypeSpec:
        if self.kind in _TYPED_KINDS and self.value_type is None:
            raise ValueError(f"{self.kind} TypeSpec requires value_type")
        if self.kind in _BARE_KINDS and self.value_type is not None:
            raise ValueError(f"{self.kind} TypeSpec does not accept value_type")
        return self


def parse_type_spec(value: TypeSpec | dict[str, Any] | str) -> TypeSpec:
    """Parse a TypeSpec from structured input or shorthand."""

    if isinstance(value, TypeSpec):
        return value
    return TypeSpec.model_validate(value)
