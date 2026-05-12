"""
quant_strategy_tokenizer.indicators.ht_trendline
================================================
Module purpose: Hilbert transform trendline token.
Core idea: Use TA-Lib Hilbert trendline when available, or a native EMA-based phase approximation. The implementation assumes detrended phase information can produce a smoother dominant trendline; native mode is approximate.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, HTTrendlineParams, and ModuleRunContext.
Outputs: HTTrendlineReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ht_trendline'
INPUT_KIND = 'price'


@dataclass
class HTTrendlineParams(TrendParams):
    """Configuration for the ht_trendline trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    cycle_window: int = 32


@dataclass
class HTTrendlineRequest:
    data: Any
    params: HTTrendlineParams = field(default_factory=HTTrendlineParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


HTTrendlineReport = TrendReport


def normalize_input(request: HTTrendlineRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: HTTrendlineRequest) -> ModuleResult[HTTrendlineReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["HTTrendlineParams", "HTTrendlineRequest", "HTTrendlineReport", "normalize_input", "run"]
