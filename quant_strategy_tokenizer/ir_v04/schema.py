"""Minimal qst-ir/0.4 shell models.

WP1 intentionally keeps this model small. It establishes an independent v0.4
identity and canonical byte surface without introducing TypeSpec, PortSpec, or
TokenSpec v2 semantics.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quant_strategy_tokenizer.canonical_json import stable_json_bytes

IR_VERSION_V04: Literal["qst-ir/0.4"] = "qst-ir/0.4"
CANONICAL_VERSION_V04: Literal["qst-canonical/0.4"] = "qst-canonical/0.4"


def _ensure_canonical_json(value: Any, *, field_name: str) -> Any:
    try:
        stable_json_bytes(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be canonical JSON-compatible") from exc
    return value


class NodeV04(BaseModel):
    """Opaque v0.4 node shell used before TypeSpec/PortSpec land."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    token: str | None = None
    version: int | None = Field(default=None, ge=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("inputs", "params", "metadata")
    @classmethod
    def _validate_json_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        _ensure_canonical_json(value, field_name="node JSON field")
        return value


class StrategyBodyV04(BaseModel):
    """Strategy content envelope for qst-ir/0.4."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    version: int = Field(default=1, ge=1)
    nodes: list[NodeV04] = Field(default_factory=list)
    outputs: dict[str, str] = Field(default_factory=dict)

    @field_validator("outputs")
    @classmethod
    def _validate_outputs(cls, value: dict[str, str]) -> dict[str, str]:
        _ensure_canonical_json(value, field_name="strategy outputs")
        return value

    @model_validator(mode="after")
    def _unique_node_ids(self) -> StrategyBodyV04:
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("qst-ir/0.4 strategy node ids must be unique")
        return self


class StrategyIRV04(BaseModel):
    """Top-level qst-ir/0.4 shell."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ir_version: Literal["qst-ir/0.4"] = IR_VERSION_V04
    canonical_version: Literal["qst-canonical/0.4"] = CANONICAL_VERSION_V04
    strategy: StrategyBodyV04
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        _ensure_canonical_json(value, field_name="metadata")
        return value
