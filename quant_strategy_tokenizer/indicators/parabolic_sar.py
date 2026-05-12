"""
quant_strategy_tokenizer.indicators.parabolic_sar
=================================================
Purpose: Parabolic SAR trend-stop token.
Core idea: Iteratively update a trailing stop using an extreme point and acceleration factor. The implementation assumes persistent trends should tighten stops as new extremes form and flip direction when price breaches the stop.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ParabolicSARParams, and ModuleRunContext.
Outputs: ParabolicSARReport with quality, last values, trend direction, signal,
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


INDICATOR = 'parabolic_sar'
INPUT_KIND = 'ohlc'


@dataclass
class ParabolicSARParams(TrendParams):
    """Configuration for the parabolic_sar trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    acceleration: float = 0.02
    maximum: float = 0.2


@dataclass
class ParabolicSARRequest:
    data: Any
    params: ParabolicSARParams = field(default_factory=ParabolicSARParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ParabolicSARReport = TrendReport


def normalize_input(request: ParabolicSARRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: ParabolicSARRequest) -> ModuleResult[ParabolicSARReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ParabolicSARParams", "ParabolicSARRequest", "ParabolicSARReport", "normalize_input", "run"]
