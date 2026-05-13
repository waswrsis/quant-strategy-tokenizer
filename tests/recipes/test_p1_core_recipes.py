from __future__ import annotations

from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import get_registry


def test_p1_core_recipes_registered() -> None:
    registry = get_recipe_registry()

    for recipe_id in (
        "event.threshold_above",
        "event.threshold_below",
        "gate.elapsed_threshold",
        "gate.cooldown",
    ):
        recipe = registry.get(recipe_id)
        assert recipe.recipe == recipe_id
        assert recipe.version == 1


def test_p1_core_recipes_compile() -> None:
    token_registry = get_registry()
    recipe_registry = get_recipe_registry()
    cases = [
        ("event.threshold_above", {}, {"series": "$externals.series", "threshold": "$externals.threshold"}),
        ("event.threshold_below", {}, {"series": "$externals.series", "threshold": "$externals.threshold"}),
        ("gate.elapsed_threshold", {"field": "elapsed", "threshold": 10}, {"state": "$externals.state"}),
        ("gate.cooldown", {"field": "cooldown_elapsed", "threshold": 10}, {"state": "$externals.state"}),
    ]

    for recipe_id, params, inputs in cases:
        compiled = compile_recipe(
            recipe_id=recipe_id,
            recipe_version=1,
            instance_params=params,
            instance_inputs=inputs,
            instance_id=recipe_id.replace(".", "_"),
            registry=token_registry,
            recipe_registry=recipe_registry,
        )
        assert compiled.nodes
        assert compiled.outputs
