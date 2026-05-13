"""Frame type alias and validation helpers."""

from __future__ import annotations

from typing import TypeAlias

import pandas as pd

Frame: TypeAlias = pd.DataFrame


def validate_frame(value: object, *, name: str = "frame") -> pd.DataFrame:
    """Validate that a runtime value is a pandas DataFrame."""

    if not isinstance(value, pd.DataFrame):
        raise TypeError(f"{name} must be pandas.DataFrame, got {type(value).__name__}")
    return value
