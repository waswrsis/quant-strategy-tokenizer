"""Parametrized pytest test for every (token, contract) pair."""

from __future__ import annotations

from typing import Any

import pytest

import quant_strategy_tokenizer  # noqa: F401
from quant_strategy_tokenizer.tokens._contract_runner import run_contract
from quant_strategy_tokenizer.tokens.registry import get_registry


def _generate_items() -> list[object]:
    registry = get_registry()

    items: list[object] = []
    for spec in registry.list_tokens():
        for contract in spec.behavior_contract:
            items.append(
                pytest.param(
                    spec,
                    contract,
                    id=f"{spec.id}-{contract['name']}",
                )
            )

    return items


def test_registry_not_empty() -> None:
    registry = get_registry()
    assert len(registry.list_tokens()) == 17
    assert registry.is_frozen


@pytest.mark.parametrize("spec, contract", _generate_items())
@pytest.mark.golden
def test_token_contract(spec: Any, contract: dict[str, Any]) -> None:
    result = run_contract(spec, contract)
    assert result.passed, f"Contract '{result.name}' failed: {result.error}"
