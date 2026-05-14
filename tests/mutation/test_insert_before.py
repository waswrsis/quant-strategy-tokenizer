from __future__ import annotations

from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.mutation import InsertBefore, mutate_strategy
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from tests.ir.p1_fixtures import P1_MISSING_RISK_PATH_YAML


def test_insert_before_requires_target_input_name() -> None:
    ir = load_strategy(P1_MISSING_RISK_PATH_YAML)

    result = mutate_strategy(
        ir,
        InsertBefore(
            target_node_id="plan",
            target_input_name="missing",
            new_node_spec={
                "id": "risk",
                "token": "risk.position_cap",
                "params": {"max_position": 1, "symbol_key": "current_symbol"},
                "inputs": {"state": "$externals.state"},
                "primary_input": "decision",
                "primary_output": "decision",
            },
        ),
    )

    assert not result.ok
    assert "has no input" in (result.error or "")


def test_insert_before_risk_node_repairs_pretrade_path() -> None:
    ir = load_strategy(P1_MISSING_RISK_PATH_YAML)

    result = mutate_strategy(
        ir,
        InsertBefore(
            target_node_id="plan",
            target_input_name="decision",
            new_node_spec={
                "id": "risk",
                "token": "risk.position_cap",
                "v": 1,
                "params": {"max_position": 1, "symbol_key": "current_symbol"},
                "inputs": {"state": "$externals.state"},
                "primary_input": "decision",
                "primary_output": "decision",
            },
        ),
    )

    assert result.ok
    assert result.ir is not None
    assert result.ir.graph[0].id == "risk"
    assert result.ir.graph[1].inputs["decision"] == "risk.decision"
    assert result.ir.externals["state"].type == "State"
    assert validate(result.ir, profile="pretrade").ok
