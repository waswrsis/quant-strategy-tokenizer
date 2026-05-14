"""Serializable token semantic specification."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class TemporalSpec(BaseModel):
    """Temporal safety metadata for validators."""

    uses_future_data: bool = False
    window_mode: Literal[
        "none",
        "trailing",
        "centered",
        "full_sample",
        "mixed",
        "unknown",
    ] = "none"
    output_available_at: Literal[
        "same_bar_close",
        "next_bar_open",
        "end_of_window",
        "end_of_sample",
        "unknown",
    ] = "same_bar_close"
    max_lookback: int | None = None

    @field_validator("output_available_at", mode="before")
    @classmethod
    def _normalize_output_available_at(cls, value: Any) -> Any:
        if value == "bar_close":
            return "same_bar_close"
        return value


class TokenSpec(BaseModel):
    """Token semantics only; executor callables are stored in RegisteredToken."""

    id: str
    version: int = 1
    behavior_version: int = 1

    layer: Literal["computation", "infrastructure"]
    category: str

    state_tag: Literal[
        "stateless",
        "lti_recursive",
        "nonlinear_recursive",
        "discrete_fsm",
    ] = "stateless"

    purity: Literal[
        "pure",
        "contextual_read",
        "external_read",
        "external_write",
        "forbidden",
    ] = "pure"

    inputs: dict[str, str]
    outputs: dict[str, str]
    params_schema: dict[str, Any] = Field(default_factory=dict)

    temporal: TemporalSpec
    failure_policy: dict[str, Any]

    behavior_contract: list[dict[str, Any]] = Field(default_factory=list)
    usage_examples: list[dict[str, Any]] = Field(default_factory=list)

    lifecycle: Literal[
        "experimental",
        "core_candidate",
        "core_stable",
        "deprecated",
        "removed",
    ] = "core_candidate"

    description: str = ""
