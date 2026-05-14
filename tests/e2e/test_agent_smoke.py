from __future__ import annotations

import quant_strategy_tokenizer.agent as agent
from quant_strategy_tokenizer.ir.model import StrategyIR
from quant_strategy_tokenizer.parse.yaml_loader import load_strategy_file


def _load_strategy(name: str) -> StrategyIR:
    return load_strategy_file(f"strategies/{name}")


def test_agent_smoke() -> None:
    discovered = agent.discover()
    assert discovered["qst_version"] == "0.1.0"
    assert len(agent.vocabulary()) == 25
    assert len(agent.recipes()) == 9


def test_agent_discover_lists_p2_api_surface() -> None:
    discovered = agent.discover()
    agent_api = discovered["agent_api"]

    assert isinstance(agent_api, dict)
    for name in (
        "tagspec_get",
        "tagspec_verify",
        "recipe_expand",
        "diff",
        "mutate",
        "fingerprint",
        "kernel_plan",
    ):
        assert name in agent_api["p2"]


def test_agent_p2_surface_smoke() -> None:
    strategy = _load_strategy("uses_cse_duplicate_chain.qst.yaml")
    ewm_strategy = _load_strategy("uses_ewm_with_provenance.qst.yaml")

    diff = agent.diff(strategy, strategy)
    fingerprint = agent.fingerprint(strategy)
    tag = agent.tagspec_get("indicator.ewm")
    verified = agent.tagspec_verify("indicator.ewm", level="full")
    expanded = agent.recipe_expand("signals.dual_ema_cross", {"fast_span": 9, "slow_span": 21})
    kernel_plan = agent.kernel_plan(ewm_strategy)

    assert diff["graph_equal"] is True
    assert fingerprint["fingerprints"]
    assert tag is not None
    assert verified is not None and verified.verification.fully_verified is True
    assert expanded.recipe == "signals.dual_ema_cross"
    assert kernel_plan.eligible_count == 1
