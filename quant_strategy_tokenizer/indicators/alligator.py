"""
quant_strategy_tokenizer.indicators.alligator
==============================================
Module purpose: Williams Alligator trend structure token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, AlligatorParams, and ModuleRunContext.
Outputs: AlligatorReport with quality, last values, trend direction, signal,
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


INDICATOR = 'alligator'
INPUT_KIND = 'price'


@dataclass
class AlligatorParams(TrendParams):
    """Configuration for the alligator trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    jaw_window: int = 13
    teeth_window: int = 8
    lips_window: int = 5
    jaw_shift: int = 8
    teeth_shift: int = 5
    lips_shift: int = 3


@dataclass
class AlligatorRequest:
    data: Any
    params: AlligatorParams = field(default_factory=AlligatorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AlligatorReport = TrendReport


def normalize_input(request: AlligatorRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: AlligatorRequest) -> ModuleResult[AlligatorReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["AlligatorParams", "AlligatorRequest", "AlligatorReport", "normalize_input", "run"]
