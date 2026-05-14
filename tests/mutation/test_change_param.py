from __future__ import annotations

from quant_strategy_tokenizer.ir.hashing import compute_hashes
from quant_strategy_tokenizer.mutation import ChangeParam, mutate_strategy
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from tests.ir.p1_fixtures import P1_PRETRADE_READY_YAML


def test_change_param_updates_graph_node_and_hash_report() -> None:
    ir = load_strategy(P1_PRETRADE_READY_YAML)

    result = mutate_strategy(
        ir,
        ChangeParam(node_id="risk", param_name="max_position", new_value=10),
    )

    assert result.ok
    assert result.ir is not None
    assert result.ir.graph[0].params["max_position"] == 10
    assert result.before_hashes == compute_hashes(ir).as_dict()
    assert result.after_hashes == compute_hashes(result.ir).as_dict()
    assert result.before_hashes["graph_hash"] == result.after_hashes["graph_hash"]
    assert result.before_hashes["param_hash"] != result.after_hashes["param_hash"]


def test_change_param_updates_recipe_instance() -> None:
    ir = load_strategy(
        """
ir_version: qst-ir/0.3
canonical_version: qst-canonical/0.1
strategy: change_recipe_param
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
graph: []
outputs:
  value: ema.value
"""
    )

    result = mutate_strategy(
        ir,
        ChangeParam(node_id="ema", param_name="span", new_value=5),
    )

    assert result.ok
    assert result.ir is not None
    assert result.ir.recipes[0].params["span"] == 5
