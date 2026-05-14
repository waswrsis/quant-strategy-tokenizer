from __future__ import annotations

from pathlib import Path

from quant_strategy_tokenizer.execution import make_execution_plan
from quant_strategy_tokenizer.ir.canonicalize import canonicalize
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file

ROOT = Path(__file__).resolve().parents[2]


def test_duplicate_fingerprint_generates_reuse_plan_node() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "uses_cse_duplicate_chain.qst.yaml")
    canonical = canonicalize(ir)

    plan = make_execution_plan(canonical)

    assert len(canonical.graph) == 5
    assert [node.action for node in plan.nodes].count("reuse") == 2
    close_b = next(node for node in plan.nodes if node.node_id == "n1")
    max_b = next(node for node in plan.nodes if node.node_id == "n3")
    assert close_b.action == "reuse"
    assert close_b.reused_from == "n0"
    assert max_b.action == "reuse"
    assert max_b.reused_from == "n2"


def test_first_equivalent_node_computes_and_later_equivalent_node_reuses() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "uses_cse_duplicate_chain.qst.yaml")
    canonical = canonicalize(ir)

    plan = make_execution_plan(canonical)

    assert plan.nodes[0].node_id == "n0"
    assert plan.nodes[0].action == "compute"
    assert plan.nodes[1].node_id == "n1"
    assert plan.nodes[1].action == "reuse"


def test_non_equivalent_reference_strategy_nodes_do_not_reuse() -> None:
    ir = load_strategy_file(ROOT / "strategies" / "kdj_cross_basic.qst.yaml")
    canonical = canonicalize(ir)

    plan = make_execution_plan(canonical)

    assert all(node.action == "compute" for node in plan.nodes)
