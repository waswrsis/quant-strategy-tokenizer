"""
quant_strategy_tokenizer.indicators.adxr
========================================
Purpose: Average Directional Movement Rating trend-strength token.
Core idea: Compute ADXR as a smoothed average of current ADX and lagged ADX. The implementation assumes ADX is useful but noisy, so a lagged blend better represents persistent trend strength.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, ADXRParams, and ModuleRunContext.
Outputs: ADXRReport with quality, last values, trend direction, signal,
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


INDICATOR = 'adxr'
INPUT_KIND = 'ohlc'


@dataclass
class ADXRParams(TrendParams):
    """Configuration for the adxr trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 14


@dataclass
class ADXRRequest:
    data: Any
    params: ADXRParams = field(default_factory=ADXRParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


ADXRReport = TrendReport


def normalize_input(request: ADXRRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: ADXRRequest) -> ModuleResult[ADXRReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["ADXRParams", "ADXRRequest", "ADXRReport", "normalize_input", "run"]
