from __future__ import annotations

from pathlib import Path

import quant_strategy_tokenizer.agent as agent
from quant_strategy_tokenizer.mutation import ChangeParam, mutate_strategy
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]
STRATEGY = ROOT / "strategies" / "kdj_cross_basic.qst.yaml"


def test_mutate_03_strategy_stays_03_without_lineage() -> None:
    parent = load_strategy_file(STRATEGY)
    result = mutate_strategy(
        parent,
        ChangeParam(node_id="kdj", param_name="lookback", new_value=14),
    )

    assert result.ok
    assert result.ir is not None
    assert result.ir.ir_version == "qst-ir/0.3"
    assert result.ir.derived_from is None


def test_fork_then_mutate_chain_accumulates() -> None:
    parent = load_strategy_file(STRATEGY)
    forked = agent.fork(parent, "kdj_variant")

    first = mutate_strategy(
        forked,
        ChangeParam(node_id="kdj", param_name="lookback", new_value=14),
    )
    assert first.ok
    assert first.ir is not None
    assert first.ir.derived_from is not None
    assert len(first.ir.derived_from.mutation_chain) == 1
    assert first.ir.derived_from.mutation_chain[0]["kind"] == "change_param"

    second = mutate_strategy(
        first.ir,
        ChangeParam(node_id="kdj", param_name="k_alpha", new_value=0.4),
    )
    assert second.ok
    assert second.ir is not None
    assert second.ir.derived_from is not None
    assert len(second.ir.derived_from.mutation_chain) == 2
    assert second.ir.derived_from.mutation_chain[1]["param_name"] == "k_alpha"
