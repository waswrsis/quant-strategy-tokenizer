from __future__ import annotations

import quant_strategy_tokenizer.agent as agent


def test_agent_smoke() -> None:
    discovered = agent.discover()
    assert discovered["qst_version"] == "0.1.0"
    assert len(agent.vocabulary()) == 25
    assert len(agent.recipes()) == 8
