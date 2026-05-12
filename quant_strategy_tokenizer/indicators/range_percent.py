"""
quant_strategy_tokenizer.indicators.range_percent
==================================================
Purpose: calculate high-low range as a percent of price as an atomic volatility token.
Core idea: Normalize high-low range by close price. Assumes percentage range is more comparable across instruments than raw tick distance.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, RangePercentParams, and ModuleRunContext.
Outputs: RangePercentReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'range_percent'
INPUT_KIND = 'ohlc'


@dataclass
class RangePercentParams(VolatilityParams):
    """Configuration for the range_percent volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class RangePercentRequest:
    data: Any
    params: RangePercentParams = field(default_factory=RangePercentParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


RangePercentReport = VolatilityReport


def normalize_input(request: RangePercentRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: RangePercentRequest) -> ModuleResult[RangePercentReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["RangePercentParams", "RangePercentRequest", "RangePercentReport", "normalize_input", "run"]
