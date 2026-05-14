"""Recipe registry.

P0 rule:
- Built-in JSON recipes are loaded lazily.
- Registry freezes after built-ins are loaded.
- No plugin recipe support in P0.
"""

from __future__ import annotations

from importlib.resources import files

from .schema import RecipeSpec


class RecipeRegistry:
    """Mutable-until-frozen recipe registry."""

    def __init__(self) -> None:
        self._recipes: dict[tuple[str, int], RecipeSpec] = {}
        self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def register(self, spec: RecipeSpec) -> None:
        if self._frozen:
            raise RuntimeError(
                f"Recipe registry frozen; cannot register {spec.recipe}/v{spec.version}"
            )

        key = (spec.recipe, spec.version)

        if key in self._recipes:
            raise ValueError(f"Recipe {spec.recipe}/v{spec.version} already registered")

        self._recipes[key] = spec

    def freeze(self) -> None:
        self._frozen = True

    def get(self, recipe_id: str, version: int = 1) -> RecipeSpec:
        try:
            return self._recipes[(recipe_id, version)]
        except KeyError:
            raise KeyError(f"Recipe {recipe_id}/v{version} not found") from None

    def list_recipes(self, category: str | None = None) -> list[RecipeSpec]:
        recipes = sorted(self._recipes.values(), key=lambda recipe: (recipe.recipe, recipe.version))
        if category is None:
            return recipes
        return [recipe for recipe in recipes if recipe.recipe.startswith(f"{category}.")]


_RECIPE_REGISTRY = RecipeRegistry()
_RECIPES_LOADED = False


def _load_builtin_recipes() -> None:
    global _RECIPES_LOADED

    if _RECIPES_LOADED:
        return

    recipe_dirs = [
        files("quant_strategy_tokenizer.recipes.indicators"),
        files("quant_strategy_tokenizer.recipes.events"),
        files("quant_strategy_tokenizer.recipes.gates"),
        files("quant_strategy_tokenizer.recipes.algorithms"),
    ]

    for recipe_dir in recipe_dirs:
        for path in recipe_dir.iterdir():
            if not str(path).endswith(".json"):
                continue
            raw = path.read_text(encoding="utf-8")
            spec = RecipeSpec.model_validate_json(raw)
            _RECIPE_REGISTRY.register(spec)

    _RECIPES_LOADED = True


def get_recipe_registry() -> RecipeRegistry:
    """Return the frozen built-in recipe registry."""

    _load_builtin_recipes()
    if not _RECIPE_REGISTRY.is_frozen:
        _RECIPE_REGISTRY.freeze()
    return _RECIPE_REGISTRY


def get_mutable_recipe_registry_for_bootstrap() -> RecipeRegistry:
    """Internal testing/bootstrap hook."""

    return _RECIPE_REGISTRY
