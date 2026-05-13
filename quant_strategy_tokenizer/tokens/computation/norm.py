"""Normalization computation tokens."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import float_series, nan_series_like
from quant_strategy_tokenizer.tokens.registry import token


@token(
    id="norm.range_position",
    layer="computation",
    category="norm",
    inputs={
        "value": "TimeSeries[float]",
        "low": "TimeSeries[float]",
        "high": "TimeSeries[float]",
    },
    outputs={"value": "TimeSeries[float]"},
    params_schema={
        "scale": {"type": "number", "default": 1.0},
        "zero_range_policy": {
            "type": "string",
            "enum": ["error", "unknown", "zero"],
            "default": "unknown",
        },
    },
    contracts=[
        {
            "name": "basic_midpoint",
            "inputs": {"value": [5.0], "low": [0.0], "high": [10.0]},
            "params": {"scale": 100, "zero_range_policy": "unknown"},
            "expected_output": {"value": [50.0]},
        },
        {
            "name": "zero_range_policy_unknown",
            "inputs": {"value": [5.0], "low": [3.0], "high": [3.0]},
            "params": {"scale": 100, "zero_range_policy": "unknown"},
            "expected_status": "unknown",
            "expected_reason": "zero_range",
        },
    ],
    usage_examples=[{"title": "RSV component in KDJ", "see_recipe": "indicator.kdj"}],
    description="Position of a value in [low, high] scaled to a target range.",
)
def norm_range_position(
    value: pd.Series,
    low: pd.Series,
    high: pd.Series,
    scale: float = 1.0,
    zero_range_policy: Literal["error", "unknown", "zero"] = "unknown",
) -> TokenOutput:
    values = float_series(value)
    lows = float_series(low)
    highs = float_series(high)
    denominator = highs - lows
    zero_mask = denominator == 0.0
    if bool(zero_mask.any()):
        if zero_range_policy == "error":
            return TokenOutput(status="error", error_kind="zero_range", values={"value": nan_series_like(values)})
        if zero_range_policy == "zero":
            denominator = denominator.mask(zero_mask, np.nan)
            result = ((values - lows) / denominator * float(scale)).fillna(0.0)
            return TokenOutput(values={"value": result})
        result = (values - lows) / denominator.mask(zero_mask, np.nan) * float(scale)
        return TokenOutput(status="unknown", unknown_reason="zero_range", values={"value": result})
    return TokenOutput(values={"value": (values - lows) / denominator * float(scale)})
