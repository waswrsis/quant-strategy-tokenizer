"""State infrastructure tokens."""

from __future__ import annotations

from typing import Any

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens.registry import token


@token(
    id="state.read_field",
    layer="infrastructure",
    category="state",
    purity="contextual_read",
    inputs={"state": "State"},
    outputs={"value": "Number"},
    params_schema={
        "field": {"type": "string"},
        "default": {"type": "number", "default": 0},
    },
    contracts=[
        {
            "name": "reads_present_field",
            "inputs": {"state": {"cooldown_elapsed": 12}},
            "params": {"field": "cooldown_elapsed", "default": 0},
            "expected_output": {"value": 12},
        },
        {
            "name": "missing_field_returns_default",
            "inputs": {"state": {}},
            "params": {"field": "cooldown_elapsed", "default": 0},
            "expected_output": {"value": 0},
        },
    ],
    description="Read a scalar state field, returning default when missing.",
)
def state_read_field(state: dict[str, Any], field: str, default: float = 0) -> TokenOutput:
    value = state.get(field, default)
    return TokenOutput(values={"value": value})
