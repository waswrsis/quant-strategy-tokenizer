"""Data access computation tokens."""

from __future__ import annotations

import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens.registry import token


@token(
    id="data.column",
    layer="computation",
    category="data",
    inputs={"frame": "Frame"},
    outputs={"value": "TimeSeries[float]"},
    params_schema={"column": {"type": "string"}},
    contracts=[
        {
            "name": "select_close",
            "inputs": {"frame": {"close": [1.0, 2.0], "open": [3.0, 4.0]}},
            "params": {"column": "close"},
            "expected_output": {"value": [1.0, 2.0]},
        },
        {
            "name": "select_open",
            "inputs": {"frame": {"close": [1.0, 2.0], "open": [3.0, 4.0]}},
            "params": {"column": "open"},
            "expected_output": {"value": [3.0, 4.0]},
        },
    ],
    description="Select a column from a pandas DataFrame.",
)
def data_column(frame: pd.DataFrame, column: str) -> TokenOutput:
    if column not in frame.columns:
        return TokenOutput(
            status="error",
            error_kind="missing_input",
            values={"value": pd.Series(dtype=float)},
        )
    return TokenOutput(values={"value": frame[column]})


@token(
    id="data.shift",
    layer="computation",
    category="data",
    inputs={"series": "TimeSeries[float]"},
    outputs={"value": "TimeSeries[float]"},
    params_schema={"periods": {"type": "integer", "default": 1}},
    temporal={
        "uses_future_data": False,
        "window_mode": "trailing",
        "output_available_at": "same_bar_close",
        "max_lookback": None,
    },
    contracts=[
        {
            "name": "shift_by_1",
            "inputs": {"series": [1.0, 2.0, 3.0, 4.0]},
            "params": {"periods": 1},
            "expected_output": {"value": [None, 1.0, 2.0, 3.0]},
        },
        {
            "name": "shift_by_zero_identity",
            "inputs": {"series": [10.0, 20.0]},
            "params": {"periods": 0},
            "expected_output": {"value": [10.0, 20.0]},
        },
    ],
    description="Shift series by N periods.",
)
def data_shift(series: pd.Series, periods: int = 1) -> TokenOutput:
    return TokenOutput(values={"value": series.shift(periods)})
