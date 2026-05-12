"""
quant_strategy_tokenizer.indicators.macd
========================================
Module purpose: Moving Average Convergence/Divergence trend-momentum token.
Core idea: Compute fast EMA minus slow EMA, then a signal EMA and histogram. The implementation assumes convergence/divergence between two EMA horizons captures trend acceleration; histogram sign and line relation drive signal semantics.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, MACDParams, and ModuleRunContext.
Outputs: MACDReport with quality, last values, trend direction, signal,
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


INDICATOR = 'macd'
INPUT_KIND = 'price'


@dataclass
class MACDParams(TrendParams):
    """Configuration for the macd trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    fast_window: int = 12
    slow_window: int = 26
    signal_window: int = 9


@dataclass
class MACDRequest:
    data: Any
    params: MACDParams = field(default_factory=MACDParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MACDReport = TrendReport


def normalize_input(request: MACDRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: MACDRequest) -> ModuleResult[MACDReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MACDParams", "MACDRequest", "MACDReport", "normalize_input", "run"]
