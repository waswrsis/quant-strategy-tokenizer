"""Boolean logic computation tokens."""

from __future__ import annotations

import pandas as pd

from quant_strategy_tokenizer.core.output import TokenOutput
from quant_strategy_tokenizer.tokens._helpers import bool_series
from quant_strategy_tokenizer.tokens.registry import token


@token(
    id="logic.and",
    layer="computation",
    category="logic",
    inputs={"a": "TimeSeries[bool]", "b": "TimeSeries[bool]"},
    outputs={"value": "TimeSeries[bool]"},
    contracts=[
        {
            "name": "basic_and",
            "inputs": {"a": [True, True, False], "b": [True, False, True]},
            "params": {},
            "expected_output": {"value": [True, False, False]},
        },
        {
            "name": "missing_treated_false",
            "inputs": {"a": [True, None], "b": [True, True]},
            "params": {},
            "expected_output": {"value": [True, False]},
        },
    ],
    description="Elementwise boolean AND.",
)
def logic_and(a: pd.Series, b: pd.Series) -> TokenOutput:
    return TokenOutput(values={"value": bool_series(a) & bool_series(b)})
