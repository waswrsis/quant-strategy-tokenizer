from __future__ import annotations

from quant_strategy_tokenizer.ir.validate import validate
from quant_strategy_tokenizer.mutation import mutate_strategy
from quant_strategy_tokenizer.mutation.repair import mutation_from_repair_hint
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy
from tests.ir.p1_fixtures import P1_MISSING_RISK_PATH_YAML


def test_missing_risk_path_repair_hint_converts_to_insert_before() -> None:
    ir = load_strategy(P1_MISSING_RISK_PATH_YAML)
    failure = validate(ir, profile="pretrade").failures[0]
    assert failure.repair_hint is not None

    op = mutation_from_repair_hint(failure.repair_hint)
    result = mutate_strategy(ir, op)

    assert result.ok
    assert result.ir is not None
    assert validate(result.ir, profile="pretrade").ok
    assert result.ir.graph[0].token == "risk.position_cap"
    assert result.ir.graph[1].inputs["decision"] == "risk_plan.decision"
