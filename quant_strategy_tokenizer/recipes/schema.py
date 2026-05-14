"""Recipe schema models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecipeNode(BaseModel):
    """One node inside a JSON recipe graph."""

    model_config = ConfigDict(extra="forbid")

    id: str
    token: str | None = None
    recipe: str | None = None
    v: int = 1
    version: int | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    role: str | None = None

    @model_validator(mode="after")
    def _exactly_one_kind(self) -> RecipeNode:
        if (self.token is None) == (self.recipe is None):
            raise ValueError("RecipeNode must declare exactly one of token or recipe")
        return self

    @property
    def resolved_version(self) -> int:
        return self.version if self.version is not None else self.v


class RecipeSpec(BaseModel):
    """Serializable recipe specification."""

    model_config = ConfigDict(extra="forbid")

    recipe: str
    version: int = 1
    params_schema: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, str]
    outputs: dict[str, str]
    graph: list[RecipeNode]
    description: str = ""
