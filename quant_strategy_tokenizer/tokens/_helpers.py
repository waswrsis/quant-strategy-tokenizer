"""Small helpers shared by built-in token executors."""

from __future__ import annotations

import numpy as np
import pandas as pd


def float_series(series: pd.Series) -> pd.Series:
    """Return a float Series preserving the original index."""

    return pd.to_numeric(series, errors="coerce").astype(float)


def bool_series(series: pd.Series) -> pd.Series:
    """Return a bool Series with missing values treated as False."""

    return series.astype("boolean").fillna(False).astype(bool)


def nan_series_like(series: pd.Series) -> pd.Series:
    """Create a float NaN series with the same index."""

    return pd.Series(np.nan, index=series.index, dtype=float)
