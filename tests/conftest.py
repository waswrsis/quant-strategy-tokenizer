"""Shared test fixtures."""

from __future__ import annotations

import pytest

from quant_strategy_tokenizer.recipes.registry import RecipeRegistry
from quant_strategy_tokenizer.tokens.registry import Registry


@pytest.fixture
def isolated_registry() -> Registry:
    return Registry()


@pytest.fixture
def isolated_recipe_registry() -> RecipeRegistry:
    return RecipeRegistry()
