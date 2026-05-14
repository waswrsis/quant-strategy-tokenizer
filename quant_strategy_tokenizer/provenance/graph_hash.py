"""Graph template hashing for TagSpec attachment checks."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from quant_strategy_tokenizer.recipes.registry import RecipeRegistry, get_recipe_registry
from quant_strategy_tokenizer.recipes.schema import RecipeSpec


def _stable_json(payload: Any) -> str:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def recipe_graph_template_payload(spec: RecipeSpec) -> dict[str, Any]:
    """Return the deterministic recipe template payload used by TagSpec."""

    return {
        "recipe": spec.recipe,
        "version": spec.version,
        "params_schema": spec.params_schema,
        "inputs": spec.inputs,
        "outputs": spec.outputs,
        "graph": [
            node.model_dump(mode="json", exclude_none=True)
            for node in spec.graph
        ],
    }


def recipe_graph_template_hash(
    recipe_id: str,
    version: int = 1,
    *,
    recipe_registry: RecipeRegistry | None = None,
) -> str:
    """Compute the deterministic graph template hash for a recipe."""

    registry = recipe_registry or get_recipe_registry()
    spec = registry.get(recipe_id, version)
    payload = recipe_graph_template_payload(spec)
    digest = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
