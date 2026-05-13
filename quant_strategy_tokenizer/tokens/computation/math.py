"""Arithmetic computation tokens."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import float_series, nan_series_like
from quant_strategy_tokenizer.tokens.registry import token


@token(
    id="math.add",
    layer="computation",
    category="math",
    inputs={"a": "TimeSeries[float]", "b": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    contracts=[
        {
            "name": "basic_add",
            "inputs": {"a": [1.0, 2.0], "b": [3.0, 4.0]},
            "params": {},
            "expected_output": {"value": [4.0, 6.0]},
        },
        {
            "name": "nan_propagates",
            "inputs": {"a": [1.0, None], "b": [3.0, 4.0]},
            "params": {},
            "expected_output": {"value": [4.0, None]},
        },
    ],
    description="Elementwise addition.",
)
def math_add(a: pd.Series, b: pd.Series) -> TokenOutput:
    return TokenOutput(values={"value": float_series(a) + float_series(b)})


@token(
    id="math.sub",
    layer="computation",
    category="math",
    inputs={"a": "TimeSeries[float]", "b": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    contracts=[
        {
            "name": "basic_sub",
            "inputs": {"a": [5.0, 2.0], "b": [3.0, 4.0]},
            "params": {},
            "expected_output": {"value": [2.0, -2.0]},
        },
        {
            "name": "zero_result",
            "inputs": {"a": [2.0], "b": [2.0]},
            "params": {},
            "expected_output": {"value": [0.0]},
        },
    ],
    description="Elementwise subtraction.",
)
def math_sub(a: pd.Series, b: pd.Series) -> TokenOutput:
    return TokenOutput(values={"value": float_series(a) - float_series(b)})


@token(
    id="math.mul",
    layer="computation",
    category="math",
    inputs={"a": "TimeSeries[float]", "b": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    contracts=[
        {
            "name": "basic_mul",
            "inputs": {"a": [2.0, 3.0], "b": [4.0, 5.0]},
            "params": {},
            "expected_output": {"value": [8.0, 15.0]},
        },
        {
            "name": "zero_mul",
            "inputs": {"a": [2.0, 0.0], "b": [4.0, 5.0]},
            "params": {},
            "expected_output": {"value": [8.0, 0.0]},
        },
    ],
    description="Elementwise multiplication.",
)
def math_mul(a: pd.Series, b: pd.Series) -> TokenOutput:
    return TokenOutput(values={"value": float_series(a) * float_series(b)})


@token(
    id="math.div",
    layer="computation",
    category="math",
    inputs={"a": "TimeSeries[float]", "b": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    params_schema={
        "zero_policy": {
            "type": "string",
            "enum": ["error", "unknown", "inf"],
            "default": "error",
        }
    },
    contracts=[
        {
            "name": "basic_div",
            "inputs": {"a": [6.0, 4.0], "b": [3.0, 2.0]},
            "params": {"zero_policy": "error"},
            "expected_output": {"value": [2.0, 2.0]},
        },
        {
            "name": "zero_unknown",
            "inputs": {"a": [1.0], "b": [0.0]},
            "params": {"zero_policy": "unknown"},
            "expected_status": "unknown",
            "expected_reason": "division_by_zero",
        },
    ],
    description="Elementwise division with explicit zero policy.",
)
def math_div(
    a: pd.Series,
    b: pd.Series,
    zero_policy: Literal["error", "unknown", "inf"] = "error",
) -> TokenOutput:
    left = float_series(a)
    right = float_series(b)
    zero_mask = right == 0.0
    if bool(zero_mask.any()):
        if zero_policy == "error":
            return TokenOutput(
                status="error",
                error_kind="division_by_zero",
                values={"value": nan_series_like(left)},
            )
        if zero_policy == "unknown":
            result = left / right.replace(0.0, np.nan)
            return TokenOutput(
                status="unknown",
                unknown_reason="division_by_zero",
                values={"value": result},
            )
    return TokenOutput(values={"value": left / right})


@token(
    id="math.linear_combination",
    layer="computation",
    category="math",
    inputs={},
    outputs={"value": "TimeSeries[float]"},
    params_schema={
        "terms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"input": {"type": "string"}, "weight": {"type": "number"}},
                "required": ["input", "weight"],
            },
            "minItems": 1,
        }
    },
    contracts=[
        {
            "name": "three_k_minus_two_d",
            "inputs": {"k": [10.0, 20.0], "d": [1.0, 2.0]},
            "params": {"terms": [{"input": "k", "weight": 3}, {"input": "d", "weight": -2}]},
            "expected_output": {"value": [28.0, 56.0]},
        },
        {
            "name": "single_term_scale",
            "inputs": {"x": [1.0, 2.0]},
            "params": {"terms": [{"input": "x", "weight": 0.5}]},
            "expected_output": {"value": [0.5, 1.0]},
        },
    ],
    description="Weighted sum over dynamically named series inputs.",
)
def math_linear_combination(terms: list[dict[str, Any]], **series_inputs: pd.Series) -> TokenOutput:
    result: pd.Series | None = None
    for term in terms:
        name = str(term["input"])
        weight = float(term["weight"])
        if name not in series_inputs:
            return TokenOutput(
                status="error",
                error_kind="missing_input",
                values={"value": pd.Series(dtype=float)},
            )
        contribution = float_series(series_inputs[name]) * weight
        result = contribution if result is None else result.add(contribution, fill_value=np.nan)
    if result is None:
        return TokenOutput(status="error", error_kind="missing_input", values={"value": pd.Series(dtype=float)})
    return TokenOutput(values={"value": result})
