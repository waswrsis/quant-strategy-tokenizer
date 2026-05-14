"""Strategy Content IR models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from quant_strategy_tokenizer.provenance import ProvenanceTag

IR_VERSION = "qst-ir/0.3"
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
