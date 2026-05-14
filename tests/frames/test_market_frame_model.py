from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from quant_strategy_tokenizer.frames import MarketFrame, OHLCVBar


def _bar(timestamp: str, symbol: str = "BTC/USD") -> OHLCVBar:
    return OHLCVBar(
        timestamp=timestamp,
        symbol=symbol,
        open="1",
        high="2",
        low="0.5",
        close="1.5",
        volume="10",
    )


def test_market_frame_canonicalizes_symbols_rows_and_utc_timestamps() -> None:
    frame = MarketFrame(
        symbols=["ETH/USD", "BTC/USD", "BTC/USD"],
        bars=[
            _bar("2026-05-14T10:00:00+01:00", "ETH/USD"),
            _bar("2026-05-14T08:00:00Z", "BTC/USD"),
        ],
    )

    assert frame.symbols == ["BTC/USD", "ETH/USD"]
    assert [bar.symbol for bar in frame.bars] == ["BTC/USD", "ETH/USD"]
    assert frame.bars[0].timestamp == datetime(2026, 5, 14, 8, 0, tzinfo=UTC)
    assert frame.bars[1].timestamp == datetime(2026, 5, 14, 9, 0, tzinfo=UTC)


def test_market_frame_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        OHLCVBar(
            timestamp=datetime(2026, 5, 14, 8, 0),
            symbol="BTC/USD",
            open="1",
            high="1",
            low="1",
            close="1",
            volume="1",
        )


def test_market_frame_rejects_invalid_symbol() -> None:
    with pytest.raises(ValidationError, match="QSTSymbol"):
        _bar("2026-05-14T08:00:00Z", "btc/usd")


def test_market_frame_empty_is_valid() -> None:
    frame = MarketFrame()
    assert frame.symbols == []
    assert frame.bars == []


def test_market_frame_rejects_duplicate_timestamp_symbol() -> None:
    timestamp = datetime(2026, 5, 14, 8, 0, tzinfo=timezone(timedelta(hours=1)))
    with pytest.raises(ValidationError, match="Duplicate OHLCV"):
        MarketFrame(bars=[_bar(timestamp.isoformat()), _bar(timestamp.isoformat())])
