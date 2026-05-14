from __future__ import annotations

from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from quant_strategy_tokenizer.recipes.compiler import compile_recipe
from quant_strategy_tokenizer.recipes.registry import get_recipe_registry
from quant_strategy_tokenizer.tokens.registry import get_registry


def test_signals_dual_ema_cross_registered() -> None:
    registry = get_recipe_registry()

    recipe = registry.get("signals.dual_ema_cross")

    assert recipe.recipe == "signals.dual_ema_cross"
    assert recipe.version == 1
    assert len(registry.list_recipes()) == 9


def test_signals_dual_ema_cross_compiles_and_preserves_ewm_provenance() -> None:
    compiled = compile_recipe(
        recipe_id="signals.dual_ema_cross",
        recipe_version=1,
        instance_params={"fast_span": 9, "slow_span": 21, "init": "first_value"},
        instance_inputs={"series": "$externals.market.close"},
        instance_id="dual",
        registry=get_registry(),
        recipe_registry=get_recipe_registry(),
    )

    assert compiled.outputs["fast"].node_id == "dual.fast_ema.ewm"
    assert compiled.outputs["slow"].node_id == "dual.slow_ema.ewm"
    assert compiled.outputs["cross"].node_id == "dual.cross.and"
    ewm_nodes = [node for node in compiled.nodes if node.token == "smooth.linear_recursive"]
    assert len(ewm_nodes) == 2
    assert all(node.provenance[0].semantic_id == "indicator.ewm" for node in ewm_nodes)


def test_strategy_using_signals_dual_ema_cross_canonicalizes() -> None:
    ir = load_strategy(
        """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: dual_ema_cross_smoke
strategy_version: 1
form: surface
externals:
  market:
    type: Frame[OHLCV]
    required: true
recipes:
  - id: signal
    recipe: signals.dual_ema_cross
    version: 1
    params:
      fast_span: 9
      slow_span: 21
      init: first_value
    inputs:
      series: market.close
graph:
  - id: decision
    token: decision.lift_bool
    v: 1
    params:
      at: now
    inputs:
      series: signal.cross
  - id: plan
    token: plan.noop
    v: 1
    inputs:
      decision: decision
outputs:
  plan: plan
"""
    )

    canonical = canonicalize(ir)

    assert canonical.form == "canonical"
    assert any(node.provenance for node in canonical.graph if node.token == "smooth.linear_recursive")
