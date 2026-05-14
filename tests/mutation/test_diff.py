from __future__ import annotations

from quant_strategy_tokenizer.mutation import ChangeParam, diff_strategies, mutate_strategy
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from tests.ir.p1_fixtures import P1_PRETRADE_READY_YAML


def test_diff_reports_param_change_and_hash_layers() -> None:
    left = load_strategy(P1_PRETRADE_READY_YAML)
    mutation = mutate_strategy(
        left,
        ChangeParam(node_id="risk", param_name="max_position", new_value=10),
    )
    assert mutation.ok
    assert mutation.ir is not None

    diff = diff_strategies(left, mutation.ir)

    assert diff.graph_equal is True
    assert diff.param_equal is False
    assert diff.instance_equal is False
    assert diff.param_diffs[0]["path"] == "graph.risk.params.max_position"
    assert diff.left_hashes["graph_hash"] == diff.right_hashes["graph_hash"]
