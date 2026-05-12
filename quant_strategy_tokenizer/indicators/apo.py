"""
quant_strategy_tokenizer.indicators.apo
=======================================
Module purpose: Absolute Price Oscillator trend-momentum token.
Core idea: Compute the absolute fast/slow EMA spread, then a signal line and histogram. The implementation assumes raw price-distance between EMA horizons is the desired momentum unit.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, APOParams, and ModuleRunContext.
Outputs: APOReport with quality, last values, trend direction, signal,
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


INDICATOR = 'apo'
INPUT_KIND = 'price'


@dataclass
class APOParams(TrendParams):
    """Configuration for the apo trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    fast_window: int = 12
    slow_window: int = 26
    signal_window: int = 9


@dataclass
class APORequest:
    data: Any
    params: APOParams = field(default_factory=APOParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


APOReport = TrendReport


def normalize_input(request: APORequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: APORequest) -> ModuleResult[APOReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["APOParams", "APORequest", "APOReport", "normalize_input", "run"]
