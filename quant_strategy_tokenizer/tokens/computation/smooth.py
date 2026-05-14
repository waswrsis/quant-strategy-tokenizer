"""Smoothing computation tokens."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import float_series
from quant_strategy_tokenizer.tokens.registry import token


@token(
    id="smooth.linear_recursive",
    layer="computation",
    category="smooth",
    state_tag="lti_recursive",
    inputs={"series": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    params_schema={
        "alpha": {"type": "number", "minimum": 0, "maximum": 1},
        "init": {
            "oneOf": [{"type": "number"}, {"type": "string", "enum": ["first_value"]}],
            "default": "first_value",
        },
    },
    temporal={
        "uses_future_data": False,
        "window_mode": "trailing",
        "output_available_at": "same_bar_close",
        "max_lookback": None,
    },
    contracts=[
        {
            "name": "first_value_init",
            "inputs": {"series": [1.0, 2.0, 3.0]},
            "params": {"alpha": 0.5, "init": "first_value"},
            "expected_output": {"value": [1.0, 1.5, 2.25]},
        },
        {
            "name": "numeric_seed_with_nan",
            "inputs": {"series": ["NaN", 10.0]},
            "params": {"alpha": 0.25, "init": 4.0},
            "expected_output": {"value": [4.0, 5.5]},
        },
    ],
    description="Linear recursive smoother y[t] = alpha*x[t] + (1-alpha)*y[t-1].",
)
def smooth_linear_recursive(
    series: pd.Series,
    alpha: float,
    init: float | Literal["first_value"] = "first_value",
) -> TokenOutput:
    values = float_series(series)
    if values.empty:
        return TokenOutput(status="unknown", unknown_reason="insufficient_data", values={"value": values})

    out: list[float] = []
    if init == "first_value":
        first_valid = values.dropna()
        prev = float(first_valid.iloc[0]) if not first_valid.empty else np.nan
    else:
        prev = float(init)

    for raw in values:
        x = float(raw) if pd.notna(raw) else np.nan
        if np.isnan(x):
            out.append(prev)
            continue
        if init == "first_value" and not out and pd.notna(values.iloc[0]):
            prev = x
        else:
            prev = float(alpha) * x + (1.0 - float(alpha)) * prev
        out.append(prev)

    return TokenOutput(values={"value": pd.Series(out, index=values.index, dtype=float)})
