"""
quant_strategy_tokenizer.indicators.donchian_channel
====================================================
Module purpose: Donchian channel breakout trend token.
Core idea: Compute rolling highest high, lowest low, and their midpoint. The implementation assumes channel extremes define breakout context while the midpoint gives a trend reference.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, DonchianChannelParams, and ModuleRunContext.
Outputs: DonchianChannelReport with quality, last values, trend direction, signal,
optional series, input profile, used fields, warnings, and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history, or
unavailable requested backend return ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .trend_common import TrendParams, TrendReport, normalize_trend_input, run_trend_indicator


INDICATOR = 'donchian_channel'
INPUT_KIND = 'ohlc'


@dataclass
class DonchianChannelParams(TrendParams):
    """Configuration for the donchian_channel trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    channel_window: int = 20


@dataclass
class DonchianChannelRequest:
    data: Any
    params: DonchianChannelParams = field(default_factory=DonchianChannelParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DonchianChannelReport = TrendReport


def normalize_input(request: DonchianChannelRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: DonchianChannelRequest) -> ModuleResult[DonchianChannelReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["DonchianChannelParams", "DonchianChannelRequest", "DonchianChannelReport", "normalize_input", "run"]
