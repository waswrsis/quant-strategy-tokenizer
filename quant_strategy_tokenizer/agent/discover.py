"""Agent discovery response."""

from __future__ import annotations

from quant_strategy_tokenizer import __version__
from quant_strategy_tokenizer.ir.model import CANONICAL_VERSION, IR_VERSION
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import get_registry


def discover() -> dict[str, object]:
    """Return capability discovery data."""

    registry = get_registry()
    recipe_registry = get_recipe_registry()
    return {
        "qst_version": __version__,
        "ir_version": IR_VERSION,
        "canonical_version": CANONICAL_VERSION,
        "vocabulary_summary": {
            "computation_tokens": len(registry.list_tokens(layer="computation")),
            "infrastructure_tokens": len(registry.list_tokens(layer="infrastructure")),
            "recipes": len(recipe_registry.list_recipes()),
            "reference_strategies": 1,
        },
        "supported_profiles": ["research", "paper", "pretrade", "production_guarded"],
        "supported_input_kinds": ["yaml", "json"],
        "supported_detokenize_levels": ["L1"],
        "schemas_url": "/docs/JSON_SCHEMAS/",
    }
