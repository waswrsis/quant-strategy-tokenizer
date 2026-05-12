"""
quant_strategy_tokenizer.indicators.adx
=======================================
Purpose: Average Directional Index trend-strength token.
Core idea: Compute +DI, -DI, DX, and ADX from high/low/close directional movement. The implementation assumes high/low range expansion contains trend-strength information; ADX measures strength, while +DI vs -DI gives direction.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ADXParams, and ModuleRunContext.
Outputs: ADXReport with quality, last values, trend direction, signal,
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


INDICATOR = 'adx'
INPUT_KIND = 'ohlc'


@dataclass
class ADXParams(TrendParams):
    """Configuration for the adx trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 14


@dataclass
class ADXRequest:
    data: Any
    params: ADXParams = field(default_factory=ADXParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ADXReport = TrendReport


def normalize_input(request: ADXRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: ADXRequest) -> ModuleResult[ADXReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ADXParams", "ADXRequest", "ADXReport", "normalize_input", "run"]
