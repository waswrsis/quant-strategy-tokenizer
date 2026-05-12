"""
quant_strategy_tokenizer.indicators.ma_ribbon
=============================================
Module purpose: Moving-average ribbon trend-alignment token.
Core idea: Compute several moving averages and inspect their ordering and spread. The implementation assumes aligned short-to-long averages imply trend agreement, while tangled averages imply mixed trend.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, MARibbonParams, and ModuleRunContext.
Outputs: MARibbonReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ma_ribbon'
INPUT_KIND = 'price'


@dataclass
class MARibbonParams(TrendParams):
    """Configuration for the ma_ribbon trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    periods: Optional[List[int]] = field(default_factory=lambda: [5, 10, 20, 50, 100, 200])
    smoothing: str = 'ema'


@dataclass
class MARibbonRequest:
    data: Any
    params: MARibbonParams = field(default_factory=MARibbonParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MARibbonReport = TrendReport


def normalize_input(request: MARibbonRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: MARibbonRequest) -> ModuleResult[MARibbonReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MARibbonParams", "MARibbonRequest", "MARibbonReport", "normalize_input", "run"]
