"""Port contracts for Token System v2."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from quant_strategy_tokenizer.types_v2 import AvailableAt, TypeSpec, parse_type_spec


class TemporalRequirement(BaseModel):
    """Input-side requirement for upstream data availability."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_available_at: AvailableAt = "bar_close"
    allow_unsafe_future: bool = False


class PortTemporalSpec(BaseModel):
    """Output-side temporal promise for a port.

    WP2 only stores this data. WP3 owns temporal rule resolution and validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    available_at: AvailableAt = "bar_close"
    latency_bars: int = Field(default=0, ge=0)
    min_history_bars: int = Field(default=0, ge=0)
    unsafe_future: bool = False


class InputSpec(BaseModel):
    """Input port contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: TypeSpec
    temporal_requirement: TemporalRequirement | None = None

    @field_validator("type", mode="before")
    @classmethod
    def _parse_type(cls, value: Any) -> TypeSpec:
        return parse_type_spec(value)


class OutputSpec(BaseModel):
    """Output port contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: TypeSpec
    port_temporal: PortTemporalSpec | None = None

    @field_validator("type", mode="before")
    @classmethod
    def _parse_type(cls, value: Any) -> TypeSpec:
        return parse_type_spec(value)


class PortSignature(BaseModel):
    """Token node input/output signature."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    inputs: dict[str, InputSpec] = Field(default_factory=dict)
    outputs: dict[str, OutputSpec] = Field(default_factory=dict)
