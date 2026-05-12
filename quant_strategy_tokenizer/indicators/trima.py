"""
quant_strategy_tokenizer.indicators.trima
=========================================
Module purpose: Triangular moving average trend token.
Core idea: Compute a double-smoothed simple moving average that creates triangular weighting. The implementation assumes a centered-style smooth trend estimate is more useful than a fast trigger; signals are intentionally lagging.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, TRIMAParams, and ModuleRunContext.
Outputs: TRIMAReport with quality, last values, trend direction, signal,
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


INDICATOR = 'trima'
INPUT_KIND = 'price'


@dataclass
class TRIMAParams(TrendParams):
    """Configuration for the trima trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20


@dataclass
class TRIMARequest:
    data: Any
    params: TRIMAParams = field(default_factory=TRIMAParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


TRIMAReport = TrendReport


def normalize_input(request: TRIMARequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: TRIMARequest) -> ModuleResult[TRIMAReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["TRIMAParams", "TRIMARequest", "TRIMAReport", "normalize_input", "run"]
