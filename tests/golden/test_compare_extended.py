from __future__ import annotations

from quant_strategy_tokenizer.tokens._contract_runner import run_contract
from quant_strategy_tokenizer.tokens.registry import get_registry


def test_compare_ge_and_lt_contracts() -> None:
    registry = get_registry()

    for token_id in ("compare.ge", "compare.lt"):
        registered = registry.get(token_id)
        assert len(registered.spec.behavior_contract) == 2
        for contract in registered.spec.behavior_contract:
            result = run_contract(registered, contract)
            assert result.passed, result.error
