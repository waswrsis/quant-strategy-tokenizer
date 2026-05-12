"""
quant_strategy_tokenizer.indicators.mama
========================================
Module purpose: MESA Adaptive Moving Average trend token.
Core idea: Use TA-Lib MAMA when requested, or a native efficiency-ratio approximation with MAMA/FAMA lines. The implementation assumes adaptive smoothing can follow cycles and trends better than fixed-window averages; native mode is an approximation.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, MAMAParams, and ModuleRunContext.
Outputs: MAMAReport with quality, last values, trend direction, signal,
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


INDICATOR = 'mama'
INPUT_KIND = 'price'


@dataclass
class MAMAParams(TrendParams):
    """Configuration for the mama trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 10
    mama_fast_limit: float = 0.5
    mama_slow_limit: float = 0.05


@dataclass
class MAMARequest:
    data: Any
    params: MAMAParams = field(default_factory=MAMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MAMAReport = TrendReport


def normalize_input(request: MAMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: MAMARequest) -> ModuleResult[MAMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MAMAParams", "MAMARequest", "MAMAReport", "normalize_input", "run"]
