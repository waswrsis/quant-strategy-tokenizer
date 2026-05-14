from __future__ import annotations

from quant_strategy_tokenizer.composition import expand_builtin_recipe
from quant_strategy_tokenizer.composition.verifier import (
    check_temporal_safety_compatibility,
    upgrade_verification,
)
from quant_strategy_tokenizer.provenance.registry import load_tagspec_file
from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.tokens.registry import get_registry


def test_p2a3_full_verification_does_not_change_attachment_default() -> None:
    spec = load_tagspec_file("docs/tagspecs/indicator.ewm.tagspec.yaml")
    upgraded = upgrade_verification(spec)

    assert spec.verification.minimally_attached is True
    assert spec.verification.fully_verified is False
    assert upgraded.verification.fully_verified is True


def test_indicator_ewm_temporal_sanity_is_safe() -> None:
    spec = load_tagspec_file("docs/tagspecs/indicator.ewm.tagspec.yaml")

    assert check_temporal_safety_compatibility(spec)


def test_signals_dual_ema_cross_remains_expandable_without_tagspec_upgrade() -> None:
    recipe = expand_builtin_recipe("signals.dual_ema_cross")
    compiled = compile_recipe(
        recipe_id=recipe.recipe,
        recipe_version=recipe.version,
        instance_params={"fast_span": 9, "slow_span": 21, "init": "first_value"},
        instance_inputs={"series": "$externals.series"},
        instance_id="dual",
    )
    registry = get_registry()

    assert recipe.recipe == "signals.dual_ema_cross"
    assert len(compiled.nodes) >= 3
    for node in compiled.nodes:
        temporal = registry.get(node.token, node.version).spec.temporal
        assert temporal.uses_future_data is False
        assert temporal.window_mode != "unknown"
