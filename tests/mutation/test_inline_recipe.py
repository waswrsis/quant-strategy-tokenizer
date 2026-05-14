from __future__ import annotations

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.mutation import InlineRecipe, mutate_strategy
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy

INLINE_STRATEGY = """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: inline_recipe_demo
strategy_version: 1
form: surface
externals:
  market:
    type: Frame[OHLCV]
    required: true
recipes:
  - id: ema
    recipe: indicator.ewm
    version: 1
    params:
      span: 3
    inputs:
      series: market.close
graph:
  - id: threshold
    token: compare.gt
    v: 1
    params: {}
    inputs:
      a: ema.value
      b: market.open
outputs:
  signal: threshold.value
"""


def test_inline_recipe_rewrites_refs_and_preserves_hashes() -> None:
    ir = load_strategy(INLINE_STRATEGY)
    before = compute_hashes(ir).as_dict()

    result = mutate_strategy(ir, InlineRecipe(recipe_id="ema"))

    assert result.ok, result.error
    assert result.ir is not None
    assert result.ir.recipes == []
    assert result.ir.graph[0].id == "ema.ewm"
    assert result.ir.graph[1].inputs["a"] == "ema.ewm.value"
    assert result.ir.outputs["signal"] == "threshold.value"
    assert validate(result.ir).ok
    assert result.after_hashes == before


def test_inline_recipe_reports_missing_recipe() -> None:
    ir = load_strategy(INLINE_STRATEGY)

    result = mutate_strategy(ir, InlineRecipe(recipe_id="missing"))

    assert not result.ok
    assert "Recipe instance 'missing' not found" in (result.error or "")
