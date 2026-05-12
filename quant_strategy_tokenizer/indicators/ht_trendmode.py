"""
quant_strategy_tokenizer.indicators.ht_trendmode
=================================================
Module purpose: Hilbert transform trend-vs-cycle mode token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, HTTrendModeParams, and ModuleRunContext.
Outputs: HTTrendModeReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ht_trendmode'
INPUT_KIND = 'price'


@dataclass
class HTTrendModeParams(TrendParams):
    """Configuration for the ht_trendmode trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    cycle_window: int = 32


@dataclass
class HTTrendModeRequest:
    data: Any
    params: HTTrendModeParams = field(default_factory=HTTrendModeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


HTTrendModeReport = TrendReport


def normalize_input(request: HTTrendModeRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: HTTrendModeRequest) -> ModuleResult[HTTrendModeReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["HTTrendModeParams", "HTTrendModeRequest", "HTTrendModeReport", "normalize_input", "run"]
