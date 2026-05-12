"""
quant_strategy_tokenizer.indicators.ma_cross
=============================================
Module purpose: Two-line moving average cross trend token.
Core idea: tokenize one trend calculation behind the standard QST
Params/Request/Report/run interface so agents can compose it independently.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, MACrossParams, and ModuleRunContext.
Outputs: MACrossReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ma_cross'
INPUT_KIND = 'price'


@dataclass
class MACrossParams(TrendParams):
    """Configuration for the ma_cross trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    fast_window: int = 10
    slow_window: int = 30
    smoothing: str = 'ema'


@dataclass
class MACrossRequest:
    data: Any
    params: MACrossParams = field(default_factory=MACrossParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MACrossReport = TrendReport


def normalize_input(request: MACrossRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: MACrossRequest) -> ModuleResult[MACrossReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MACrossParams", "MACrossRequest", "MACrossReport", "normalize_input", "run"]
