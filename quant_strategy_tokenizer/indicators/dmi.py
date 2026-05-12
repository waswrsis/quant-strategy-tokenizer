"""
quant_strategy_tokenizer.indicators.dmi
=======================================
Module purpose: Directional Movement Index token.
Core idea: Compute +DI and -DI from high/low directional movement and use their spread as the primary value. The implementation assumes directional range expansion identifies whether buyers or sellers dominate.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, DMIParams, and ModuleRunContext.
Outputs: DMIReport with quality, last values, trend direction, signal,
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


INDICATOR = 'dmi'
INPUT_KIND = 'ohlc'


@dataclass
class DMIParams(TrendParams):
    """Configuration for the dmi trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 14


@dataclass
class DMIRequest:
    data: Any
    params: DMIParams = field(default_factory=DMIParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


DMIReport = TrendReport


def normalize_input(request: DMIRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: DMIRequest) -> ModuleResult[DMIReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["DMIParams", "DMIRequest", "DMIReport", "normalize_input", "run"]
