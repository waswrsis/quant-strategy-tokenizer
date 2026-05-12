"""
quant_strategy_tokenizer.indicators.chandelier_exit
===================================================
Purpose: Chandelier Exit trend-stop token.
Core idea: Compute long and short trailing stops from rolling extremes minus or plus an ATR multiple. The implementation assumes stops should hang from recent extremes and widen with volatility.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ChandelierExitParams, and ModuleRunContext.
Outputs: ChandelierExitReport with quality, last values, trend direction, signal,
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


INDICATOR = 'chandelier_exit'
INPUT_KIND = 'ohlc'


@dataclass
class ChandelierExitParams(TrendParams):
    """Configuration for the chandelier_exit trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    channel_window: int = 22
    atr_window: int = 22
    multiplier: float = 3.0


@dataclass
class ChandelierExitRequest:
    data: Any
    params: ChandelierExitParams = field(default_factory=ChandelierExitParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ChandelierExitReport = TrendReport


def normalize_input(request: ChandelierExitRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: ChandelierExitRequest) -> ModuleResult[ChandelierExitReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ChandelierExitParams", "ChandelierExitRequest", "ChandelierExitReport", "normalize_input", "run"]
