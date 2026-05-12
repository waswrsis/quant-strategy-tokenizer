"""
quant_strategy_tokenizer.indicators.ht_phasor
=============================================
Module purpose: Hilbert transform phasor token.
Core idea: Compute in-phase and quadrature components using TA-Lib or native detrended/derivative approximations. The implementation assumes phase components summarize local cycle state; native mode is approximate.
Inputs: raw market data supplied by the caller, DataFrameSpec field mapping,
optional ExtractorSpec, HTPhasorParams, and ModuleRunContext.
Outputs: HTPhasorReport with quality, last values, trend direction, signal,
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


INDICATOR = 'ht_phasor'
INPUT_KIND = 'price'


@dataclass
class HTPhasorParams(TrendParams):
    """Configuration for the ht_phasor trend token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and algorithm fields below control this specific indicator.
    """

    cycle_window: int = 32


@dataclass
class HTPhasorRequest:
    data: Any
    params: HTPhasorParams = field(default_factory=HTPhasorParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


HTPhasorReport = TrendReport


def normalize_input(request: HTPhasorRequest):
    return normalize_trend_input(request, INPUT_KIND)


def run(request: HTPhasorRequest) -> ModuleResult[HTPhasorReport]:
    return run_trend_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["HTPhasorParams", "HTPhasorRequest", "HTPhasorReport", "normalize_input", "run"]
