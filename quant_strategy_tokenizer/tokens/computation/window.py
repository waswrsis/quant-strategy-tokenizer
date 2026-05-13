"""Rolling window computation tokens."""

from __future__ import annotations

import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import float_series
from quant_strategy_tokenizer.tokens.registry import token


def _window_output(series: pd.Series, window: int, op: str) -> tuple[pd.Series, bool]:
    values = float_series(series)
    result = getattr(values.rolling(window=window, min_periods=window), op)()
    return result, len(values) < window


@token(
    id="window.max",
    layer="computation",
    category="window",
    inputs={"series": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    params_schema={"window": {"type": "integer", "minimum": 1}},
    contracts=[
        {
            "name": "rolling_max_3",
            "inputs": {"series": [1.0, 3.0, 2.0, 4.0]},
            "params": {"window": 3},
            "expected_output": {"value": [None, None, 3.0, 4.0]},
        },
        {
            "name": "insufficient_data_unknown",
            "inputs": {"series": [1.0, 2.0]},
            "params": {"window": 3},
            "expected_status": "unknown",
            "expected_reason": "insufficient_data",
        },
    ],
    description="Rolling maximum with full-window warmup.",
)
def window_max(series: pd.Series, window: int) -> TokenOutput:
    result, insufficient = _window_output(series, window, "max")
    if insufficient:
        return TokenOutput(status="unknown", unknown_reason="insufficient_data", values={"value": result})
    return TokenOutput(values={"value": result})


@token(
    id="window.min",
    layer="computation",
    category="window",
    inputs={"series": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    params_schema={"window": {"type": "integer", "minimum": 1}},
    contracts=[
        {
            "name": "rolling_min_3",
            "inputs": {"series": [4.0, 3.0, 5.0, 2.0]},
            "params": {"window": 3},
            "expected_output": {"value": [None, None, 3.0, 2.0]},
        },
        {
            "name": "insufficient_data_unknown",
            "inputs": {"series": [1.0, 2.0]},
            "params": {"window": 4},
            "expected_status": "unknown",
            "expected_reason": "insufficient_data",
        },
    ],
    description="Rolling minimum with full-window warmup.",
)
def window_min(series: pd.Series, window: int) -> TokenOutput:
    result, insufficient = _window_output(series, window, "min")
    if insufficient:
        return TokenOutput(status="unknown", unknown_reason="insufficient_data", values={"value": result})
    return TokenOutput(values={"value": result})
