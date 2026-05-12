"""
quant_strategy_tokenizer.indicators.atr_trailing_stop
=====================================================
Module purpose: ATR trailing stop trend token.
Core idea: Compute long and short trailing stops around close using ATR multiples and flip when price crosses the active stop. The implementation assumes volatility-scaled trailing levels can describe trend state and exit pressure.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ATRTrailingStopParams, and ModuleRunContext.
Outputs: ATRTrailingStopReport with quality, last values, trend direction, signal,
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


INDICATOR = 'atr_trailing_stop'
INPUT_KIND = 'ohlc'


@dataclass
class ATRTrailingStopParams(TrendParams):
    """Configuration for the atr_trailing_stop trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    atr_window: int = 14
    multiplier: float = 3.0


@dataclass
class ATRTrailingStopRequest:
    data: Any
    params: ATRTrailingStopParams = field(default_factory=ATRTrailingStopParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ATRTrailingStopReport = TrendReport


def normalize_input(request: ATRTrailingStopRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: ATRTrailingStopRequest) -> ModuleResult[ATRTrailingStopReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ATRTrailingStopParams", "ATRTrailingStopRequest", "ATRTrailingStopReport", "normalize_input", "run"]
