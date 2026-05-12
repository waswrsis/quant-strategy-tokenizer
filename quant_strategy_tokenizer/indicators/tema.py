"""
quant_strategy_tokenizer.indicators.tema
========================================
Module purpose: Triple exponential moving average trend token.
Core idea: Compute TEMA from the first, second, and third EMA layers. The implementation assumes deeper EMA lag correction gives a faster trend line, with the tradeoff that turning points and noise may be emphasized.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, TEMAParams, and ModuleRunContext.
Outputs: TEMAReport with quality, last values, trend direction, signal,
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


INDICATOR = 'tema'
INPUT_KIND = 'price'


@dataclass
class TEMAParams(TrendParams):
    """Configuration for the tema trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class TEMARequest:
    data: Any
    params: TEMAParams = field(default_factory=TEMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


TEMAReport = TrendReport


def normalize_input(request: TEMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: TEMARequest) -> ModuleResult[TEMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["TEMAParams", "TEMARequest", "TEMAReport", "normalize_input", "run"]
