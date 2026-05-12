"""
quant_strategy_tokenizer.indicators.range_expansion
====================================================
Purpose: calculate current range expansion versus recent baseline as an atomic volatility token.
Core idea: Divide current high-low range by prior rolling average range. Assumes abrupt expansion flags volatility shocks relative to local history.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RangeExpansionParams, and ModuleRunContext.
Outputs: RangeExpansionReport with quality, last values, volatility direction, volatility
level, signal, regime, optional series, input profile, used fields, warnings,
and diagnostics.
Failure semantics: invalid parameters, missing fields, insufficient history,
unavailable requested backend, or invalid zero-denominator calculations return
ModuleResult.fail without hidden fallback.
Market generalization: works on caller-mapped numeric fields and does not assume
asset class, venue, quote currency, session model, or live exchange access.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..contracts import DataFrameSpec, ExtractorSpec, ModuleResult, ModuleRunContext
from .volatility_common import VolatilityParams, VolatilityReport, normalize_volatility_input, run_volatility_indicator


INDICATOR = 'range_expansion'
INPUT_KIND = 'ohlc'


@dataclass
class RangeExpansionParams(VolatilityParams):
    """Configuration for the range_expansion volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class RangeExpansionRequest:
    data: Any
    params: RangeExpansionParams = field(default_factory=RangeExpansionParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RangeExpansionReport = VolatilityReport


def normalize_input(request: RangeExpansionRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: RangeExpansionRequest) -> ModuleResult[RangeExpansionReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RangeExpansionParams", "RangeExpansionRequest", "RangeExpansionReport", "normalize_input", "run"]
