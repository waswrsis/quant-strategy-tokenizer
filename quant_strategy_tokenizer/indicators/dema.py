"""
quant_strategy_tokenizer.indicators.dema
=========================================
Module purpose: Double exponential moving average trend token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, DEMAParams, and ModuleRunContext.
Outputs: DEMAReport with quality, last values, trend direction, signal,
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


INDICATOR = 'dema'
INPUT_KIND = 'price'


@dataclass
class DEMAParams(TrendParams):
    """Configuration for the dema trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class DEMARequest:
    data: Any
    params: DEMAParams = field(default_factory=DEMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DEMAReport = TrendReport


def normalize_input(request: DEMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: DEMARequest) -> ModuleResult[DEMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["DEMAParams", "DEMARequest", "DEMAReport", "normalize_input", "run"]
