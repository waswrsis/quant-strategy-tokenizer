"""
quant_strategy_tokenizer.indicators.gmma
=========================================
Module purpose: Guppy Multiple Moving Average trend token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, GMMAParams, and ModuleRunContext.
Outputs: GMMAReport with quality, last values, trend direction, signal,
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


INDICATOR = 'gmma'
INPUT_KIND = 'price'


@dataclass
class GMMAParams(TrendParams):
    """Configuration for the gmma trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    short_periods: Optional[List[int]] = field(default_factory=lambda: [3, 5, 8, 10, 12, 15])
    long_periods: Optional[List[int]] = field(default_factory=lambda: [30, 35, 40, 45, 50, 60])


@dataclass
class GMMARequest:
    data: Any
    params: GMMAParams = field(default_factory=GMMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


GMMAReport = TrendReport


def normalize_input(request: GMMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: GMMARequest) -> ModuleResult[GMMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["GMMAParams", "GMMARequest", "GMMAReport", "normalize_input", "run"]
