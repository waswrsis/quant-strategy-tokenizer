"""
quant_strategy_tokenizer.indicators.aroon
==========================================
Module purpose: Aroon up/down trend timing token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, AroonParams, and ModuleRunContext.
Outputs: AroonReport with quality, last values, trend direction, signal,
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


INDICATOR = 'aroon'
INPUT_KIND = 'ohlc'


@dataclass
class AroonParams(TrendParams):
    """Configuration for the aroon trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 25


@dataclass
class AroonRequest:
    data: Any
    params: AroonParams = field(default_factory=AroonParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AroonReport = TrendReport


def normalize_input(request: AroonRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: AroonRequest) -> ModuleResult[AroonReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["AroonParams", "AroonRequest", "AroonReport", "normalize_input", "run"]
