"""Comparison computation tokens."""

from __future__ import annotations

import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import float_series
from quant_strategy_tokenizer.tokens.registry import token


@token(
    id="compare.gt",
    layer="computation",
    category="compare",
    inputs={"a": "TimeSeries[float]", "b": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[bool]"},
    contracts=[
        {
            "name": "basic_gt",
            "inputs": {"a": [1.0, 5.0, 3.0], "b": [4.0, 2.0, 3.0]},
            "params": {},
            "expected_output": {"value": [False, True, False]},
        },
        {
            "name": "nan_returns_false",
            "inputs": {"a": [1.0, None], "b": [0.5, 0.5]},
            "params": {},
            "expected_output": {"value": [True, False]},
        },
    ],
    description="Elementwise greater-than comparison.",
)
def compare_gt(a: pd.Series, b: pd.Series) -> TokenOutput:
    return TokenOutput(values={"value": float_series(a) > float_series(b)})


@token(
    id="compare.le",
    layer="computation",
    category="compare",
    inputs={"a": "TimeSeries[float]", "b": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[bool]"},
    contracts=[
        {
            "name": "basic_le",
            "inputs": {"a": [1.0, 5.0, 3.0], "b": [4.0, 2.0, 3.0]},
            "params": {},
            "expected_output": {"value": [True, False, True]},
        },
        {
            "name": "nan_returns_false",
            "inputs": {"a": [None], "b": [0.5]},
            "params": {},
            "expected_output": {"value": [False]},
        },
    ],
    description="Elementwise less-than-or-equal comparison.",
)
def compare_le(a: pd.Series, b: pd.Series) -> TokenOutput:
    return TokenOutput(values={"value": float_series(a) <= float_series(b)})
