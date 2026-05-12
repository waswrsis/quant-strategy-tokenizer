"""
quant_strategy_tokenizer.indicators.chande_trend_meter
======================================================
Module purpose: Chande-style composite trend meter token.
Core idea: Score trend agreement from EMA position, EMA alignment, DMI direction, ADX strength, ROC, and RSI. The implementation assumes multiple simple confirmations are more robust than a single trend indicator.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ChandeTrendMeterParams, and ModuleRunContext.
Outputs: ChandeTrendMeterReport with quality, last values, trend direction, signal,
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


INDICATOR = 'chande_trend_meter'
INPUT_KIND = 'ohlc'


@dataclass
class ChandeTrendMeterParams(TrendParams):
    """Configuration for the chande_trend_meter trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 14
    fast_window: int = 12
    slow_window: int = 26
    atr_window: int = 14


@dataclass
class ChandeTrendMeterRequest:
    data: Any
    params: ChandeTrendMeterParams = field(default_factory=ChandeTrendMeterParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ChandeTrendMeterReport = TrendReport


def normalize_input(request: ChandeTrendMeterRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: ChandeTrendMeterRequest) -> ModuleResult[ChandeTrendMeterReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ChandeTrendMeterParams", "ChandeTrendMeterRequest", "ChandeTrendMeterReport", "normalize_input", "run"]
