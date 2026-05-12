"""
quant_strategy_tokenizer.indicators.t3
======================================
Purpose: Tillson T3 moving average trend token.
Core idea: Compute a multi-stage EMA blend using the Tillson volume factor. The implementation assumes repeated smoothing plus controlled overshoot can produce a cleaner trend line than a basic EMA.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, T3Params, and ModuleRunContext.
Outputs: T3Report with quality, last values, trend direction, signal,
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


INDICATOR = 't3'
INPUT_KIND = 'price'


@dataclass
class T3Params(TrendParams):
    """Configuration for the t3 trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    window: int = 20
    vfactor: float = 0.7


@dataclass
class T3Request:
    data: Any
    params: T3Params = field(default_factory=T3Params)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


T3Report = TrendReport


def normalize_input(request: T3Request):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: T3Request) -> ModuleResult[T3Report]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["T3Params", "T3Request", "T3Report", "normalize_input", "run"]
