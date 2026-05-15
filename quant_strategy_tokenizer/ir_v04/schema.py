"""Minimal qst-ir/0.4 shell models.

WP1 established the independent v0.4 identity. WP2 adds structured signature
and canonical token reference shells without connecting legacy runtime paths.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from quant_strategy_tokenizer.canonical_json import stable_json_bytes
from quant_strategy_tokenizer.ports_v2 import PortSignature

IR_VERSION_V04: Literal["qst-ir/0.4"] = "qst-ir/0.4"
CANONICAL_VERSION_V04: Literal["qst-canonical/0.4"] = "qst-canonical/0.4"
IR_SCHEMA_VERSION_V04: Literal["qst-ir-schema/0.4"] = "qst-ir-schema/0.4"
CapabilityV04 = Literal[
    "core",
    "panel",
    "panel_type",
    "panel_ops",
    "panel_weights",
    "panel_recipes",
    "custom_token_runtime",
]
MIGRATION_TOOL_VERSION_V04: Literal["qst-migrate/0.4.0"] = "qst-migrate/0.4.0"


def _default_capabilities() -> list[CapabilityV04]:
    return ["core"]


def _ensure_canonical_json(value: Any, *, field_name: str) -> Any:
    try:
        stable_json_bytes(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be canonical JSON-compatible") from exc
    return value


class TokenRefV04(BaseModel):
    """Canonical token reference for qst-ir/0.4 nodes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    namespace: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: int = Field(ge=1)
    behavior_version: int = Field(ge=1)


class MigrationLineageV04(BaseModel):
    """Historical lineage for a legacy-to-v0.4 IR migration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["ir_migration"] = "ir_migration"
    source_ir_version: Literal["qst-ir/0.3", "qst-ir/0.3.1"]
    source_instance_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_strategy: str
    source_strategy_version: int = Field(ge=1)
    target_core_registry_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    migration_tool_version: Literal["qst-migrate/0.4.0"] = MIGRATION_TOOL_VERSION_V04


class NodeV04(BaseModel):
    """Opaque v0.4 node shell used before TypeSpec/PortSpec land."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    token: str | None = None
    version: int | None = Field(default=None, ge=1)
    token_ref: TokenRefV04 | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    signature: PortSignature = Field(default_factory=PortSignature)
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

    schema_version: Literal["qst-ir-schema/0.4"] = IR_SCHEMA_VERSION_V04
    ir_version: Literal["qst-ir/0.4"] = IR_VERSION_V04
    canonical_version: Literal["qst-canonical/0.4"] = CANONICAL_VERSION_V04
    capabilities: list[CapabilityV04] = Field(default_factory=_default_capabilities)
    strategy: StrategyBodyV04
    metadata: dict[str, Any] = Field(default_factory=dict)
    derived_from: MigrationLineageV04 | None = None

    @field_validator("metadata")
    @classmethod
    def _validate_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        _ensure_canonical_json(value, field_name="metadata")
        return value

    @field_validator("capabilities")
    @classmethod
    def _validate_capabilities(cls, value: list[CapabilityV04]) -> list[CapabilityV04]:
        if len(value) != len(set(value)):
            raise ValueError("qst-ir/0.4 capabilities must be unique")
        if "core" not in value:
            raise ValueError('qst-ir/0.4 capabilities must include "core"')
        return sorted(value)
