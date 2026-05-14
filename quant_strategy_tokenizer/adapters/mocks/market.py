"""Mock market data adapters."""

from __future__ import annotations

from typing import ClassVar

from quant_strategy_tokenizer.adapters.mocks.common import adapter_identity
from quant_strategy_tokenizer.artifacts.base import AdapterIdentity
from quant_strategy_tokenizer.frames import MarketFrame
from quant_strategy_tokenizer.frames.io.csv_io import read_csv_frame
from quant_strategy_tokenizer.frames.io.json_io import Frame
from quant_strategy_tokenizer.frames.io.parquet_io import read_parquet_frame
from quant_strategy_tokenizer.ports import MarketLoadRequest


def _ensure_market_frame(frame: Frame) -> MarketFrame:
    if not isinstance(frame, MarketFrame):
        raise TypeError(f"Expected qst-market-frame/1, got {frame.frame_version!r}")
    return frame


def _filter_symbols(frame: MarketFrame, symbols: list[str]) -> MarketFrame:
    if not symbols:
        return frame
    allowed = set(symbols)
    return MarketFrame(
        symbols=symbols,
        bars=[bar for bar in frame.bars if bar.symbol in allowed],
    )


class CsvMarketAdapter:
    """Load P4 MarketFrame CSV files."""

    capabilities: ClassVar[list[str]] = ["market_data", "csv"]

    def get_identity(self) -> AdapterIdentity:
        return adapter_identity("mock-csv-market")

    def load_market(self, request: MarketLoadRequest) -> MarketFrame:
        frame = _ensure_market_frame(read_csv_frame(request.source, "qst-market-frame/1"))
        return _filter_symbols(frame, request.symbols)


class ParquetMarketAdapter:
    """Load P4 MarketFrame Parquet files."""

    capabilities: ClassVar[list[str]] = ["market_data", "parquet"]

    def get_identity(self) -> AdapterIdentity:
        return adapter_identity("mock-parquet-market")

    def load_market(self, request: MarketLoadRequest) -> MarketFrame:
        frame = _ensure_market_frame(read_parquet_frame(request.source, "qst-market-frame/1"))
        return _filter_symbols(frame, request.symbols)
