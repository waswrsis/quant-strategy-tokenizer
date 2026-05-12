"""
quant_strategy_tokenizer.indicators.average_range
==================================================
Purpose: calculate rolling average bar range as an atomic volatility token.
Core idea: Average high-low ranges over a window. Assumes repeated intrabar spread summarizes ordinary short-horizon volatility.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, AverageRangeParams, and ModuleRunContext.
Outputs: AverageRangeReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'average_range'
INPUT_KIND = 'ohlc'


@dataclass
class AverageRangeParams(VolatilityParams):
    """Configuration for the average_range volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 20


@dataclass
class AverageRangeRequest:
    data: Any
    params: AverageRangeParams = field(default_factory=AverageRangeParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


AverageRangeReport = VolatilityReport


def normalize_input(request: AverageRangeRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: AverageRangeRequest) -> ModuleResult[AverageRangeReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["AverageRangeParams", "AverageRangeRequest", "AverageRangeReport", "normalize_input", "run"]
