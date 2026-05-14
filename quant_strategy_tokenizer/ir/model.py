"""Strategy Content IR models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quant_strategy_tokenizer.provenance import ProvenanceTag

IR_VERSION = "qst-ir/0.3"
IR_VERSION_P3_LINEAGE = "qst-ir/0.3.1"
SUPPORTED_IR_VERSIONS = (IR_VERSION, IR_VERSION_P3_LINEAGE)
CANONICAL_VERSION = "qst-canonical/0.1"


class ExternalSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    required: bool = True


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    token: str
    v: int = 1
    params: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    provenance: list[ProvenanceTag] = Field(default_factory=list)


class RecipeInstance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    recipe: str
    version: int = 1
    params: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)


class DerivedFrom(BaseModel):
    """P3b-1 inert lineage metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    parent_instance_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    parent_strategy: str | None = None
    parent_package: str | None = None
    parent_package_version: str | None = None
    mutation_chain: list[dict[str, Any]] = Field(default_factory=list)


class StrategyIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ir_version: str = IR_VERSION
    canonical_version: str = CANONICAL_VERSION
    strategy: str
    strategy_version: int = 1
    form: Literal["surface", "canonical"] = "surface"
    externals: dict[str, ExternalSpec] = Field(default_factory=dict)
    recipes: list[RecipeInstance] = Field(default_factory=list)
    graph: list[GraphNode] = Field(default_factory=list)
    outputs: dict[str, str] = Field(default_factory=dict)
    derived_from: DerivedFrom | None = None

    @model_validator(mode="after")
    def _check_ir_version(self) -> StrategyIR:
        if self.ir_version not in SUPPORTED_IR_VERSIONS:
            raise ValueError(f"Unsupported ir_version: {self.ir_version!r}")
        if self.ir_version == IR_VERSION and self.derived_from is not None:
            raise ValueError("qst-ir/0.3 strategies cannot have derived_from; use qst-ir/0.3.1")
        return self
