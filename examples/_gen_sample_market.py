"""Generate deterministic 15m BTC OHLCV sample data for P0 demos."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    rng = np.random.default_rng(20260101)
    rows = 200
    timestamps = pd.date_range("2025-01-01T00:00:00Z", periods=rows, freq="15min")
    drift = np.linspace(0, 420, rows)
    seasonal = np.sin(np.linspace(0, 12, rows)) * 120
    noise = rng.normal(0, 35, rows).cumsum()
    close = 43000 + drift + seasonal + noise
    spread = rng.uniform(25, 95, rows)
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.uniform(25, 180, rows)

    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": np.round(open_, 2),
            "high": np.round(high, 2),
            "low": np.round(low, 2),
            "close": np.round(close, 2),
            "volume": np.round(volume, 4),
        }
    )
    output = Path(__file__).with_name("sample_market_btc_15m.csv")
    frame.to_csv(output, index=False)


if __name__ == "__main__":
    main()
