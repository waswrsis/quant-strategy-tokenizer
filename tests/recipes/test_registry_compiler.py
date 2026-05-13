from __future__ import annotations

import pytest

from quant_strategy_tokenizer.recipes.compiler import CycleError, compile_recipe
from quant_strategy_tokenizer.recipes.registry import RecipeRegistry, get_recipe_registry
from quant_strategy_tokenizer.recipes.schema import RecipeSpec
from quant_strategy_tokenizer.tokens.registry import get_registry


def test_recipe_registry_loads_and_freezes() -> None:
    registry = get_recipe_registry()
    assert registry.is_frozen
    assert len(registry.list_recipes()) == 8


def test_kdj_recipe_compiles_nested_rma() -> None:
    compiled = compile_recipe(
        recipe_id="indicator.kdj",
        recipe_version=1,
        instance_params={"lookback": 9, "k_alpha": 0.3333333, "d_alpha": 0.3333333, "init": 50},
        instance_inputs={
            "high": "$externals.market.high",
            "low": "$externals.market.low",
            "close": "$externals.market.close",
        },
        instance_id="kdj",
        registry=get_registry(),
        recipe_registry=get_recipe_registry(),
    )
    assert len(compiled.nodes) == 6
    assert compiled.outputs["k"].node_id == "kdj.k.rma"
    assert compiled.outputs["d"].node_id == "kdj.d.rma"


def test_recipe_cycle_detection(isolated_recipe_registry: RecipeRegistry) -> None:
    recipe_a = RecipeSpec.model_validate(
        {
            "recipe": "test.a",
            "version": 1,
            "inputs": {"series": "TimeSeries[float]"},
            "outputs": {"value": "b.value"},
            "graph": [
                {
                    "id": "b",
                    "recipe": "test.b",
                    "v": 1,
                    "inputs": {"series": "$inputs.series"},
                }
            ],
        }
    )
    recipe_b = RecipeSpec.model_validate(
        {
            "recipe": "test.b",
            "version": 1,
            "inputs": {"series": "TimeSeries[float]"},
            "outputs": {"value": "a.value"},
            "graph": [
                {
                    "id": "a",
                    "recipe": "test.a",
                    "v": 1,
                    "inputs": {"series": "$inputs.series"},
                }
            ],
        }
    )
    isolated_recipe_registry.register(recipe_a)
    isolated_recipe_registry.register(recipe_b)

    with pytest.raises(CycleError):
        compile_recipe(
            recipe_id="test.a",
            recipe_version=1,
            instance_params={},
            instance_inputs={"series": "$externals.series"},
            instance_id="x",
            registry=get_registry(),
            recipe_registry=isolated_recipe_registry,
        )
