"""TimeSeries type alias and validation helpers."""

from __future__ import annotations

from typing import TypeAlias

import pandas as pd

TimeSeries: TypeAlias = pd.Series


def validate_timeseries(value: object, *, name: str = "series") -> pd.Series:
    """Validate that a runtime value is a pandas Series."""

    if not isinstance(value, pd.Series):
        raise TypeError(f"{name} must be pandas.Series, got {type(value).__name__}")
    return value
