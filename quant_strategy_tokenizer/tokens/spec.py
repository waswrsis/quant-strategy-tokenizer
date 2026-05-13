"""Serializable token semantic specification."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


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

    temporal: dict[str, Any]
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
