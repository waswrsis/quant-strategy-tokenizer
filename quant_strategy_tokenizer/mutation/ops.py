"""P2b-0 mutation operation models."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class ChangeParam(BaseModel):
    """Change one param on a graph node or recipe instance."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    param_name: str
    new_value: Any
    kind: Literal["change_param"] = "change_param"


class InsertBefore(BaseModel):
    """Insert a primitive graph node before one named input on a target node."""

    model_config = ConfigDict(extra="forbid")

    target_node_id: str
    target_input_name: str
    new_node_spec: dict[str, Any]
    kind: Literal["insert_before"] = "insert_before"


class ReplaceToken(BaseModel):
    """Replace one graph node token with a type-compatible token."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    new_token: str
    new_version: int = 1
    new_params: dict[str, Any] = Field(default_factory=dict)
    input_mapping: dict[str, str] = Field(default_factory=dict)
    kind: Literal["replace_token"] = "replace_token"


class InlineRecipe(BaseModel):
    """Inline one surface recipe instance into primitive graph nodes."""

    model_config = ConfigDict(extra="forbid")

    recipe_id: str
    kind: Literal["inline_recipe"] = "inline_recipe"


MutationOp = Annotated[
    ChangeParam | InsertBefore | ReplaceToken | InlineRecipe,
    Field(discriminator="kind"),
]
_OP_ADAPTER: TypeAdapter[MutationOp] = TypeAdapter(MutationOp)


def parse_mutation_op(raw: dict[str, Any]) -> MutationOp:
    """Parse a mutation op from JSON-compatible data."""

    return _OP_ADAPTER.validate_python(raw)
