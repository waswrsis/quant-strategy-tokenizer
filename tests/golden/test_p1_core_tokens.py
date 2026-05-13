from __future__ import annotations

from quant_strategy_tokenizer.tokens.registry import get_registry

P1_CORE_TOKENS = {
    ("state.read_field", 1),
    ("risk.position_cap", 1),
    ("risk.notional_cap", 1),
    ("plan.order_intent", 1),
    ("decision.map_status", 1),
    ("decision.reduce", 2),
    ("compare.ge", 1),
    ("compare.lt", 1),
}


def test_p1_core_tokens_registered_with_contracts() -> None:
    registry = get_registry()

    for token_id, version in P1_CORE_TOKENS:
        registered = registry.get(token_id, version)
        assert registered.spec.behavior_contract
        assert registered.spec.lifecycle == "core_candidate"
