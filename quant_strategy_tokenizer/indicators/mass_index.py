"""
quant_strategy_tokenizer.indicators.mass_index
===============================================
Purpose: calculate Mass Index as an atomic volatility-range token.
Core idea: Sum the ratio of single and double EMA range. Assumes repeated range bulges can warn about reversal risk without choosing direction.
Inputs: raw caller-supplied market data, DataFrameSpec field mapping, optional
ExtractorSpec, MassIndexParams, and ModuleRunContext.
Outputs: MassIndexReport with quality, last values, volatility direction, volatility
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


INDICATOR = 'mass_index'
INPUT_KIND = 'ohlc'


@dataclass
class MassIndexParams(VolatilityParams):
    """Configuration for the mass_index volatility token.

    Configuration:
    - `backend`: `native`, `talib`, or `auto`; TA-Lib is optional.
    - field names are logical names resolved by DataFrameSpec.
    - window and threshold fields shape report semantics only; this module does
      not place trades or fetch data.
    """

    window: int = 25
    fast_window: int = 9


@dataclass
class MassIndexRequest:
    data: Any
    params: MassIndexParams = field(default_factory=MassIndexParams)
    spec: DataFrameSpec = field(default_factory=DataFrameSpec)
    extractor: Optional[ExtractorSpec] = None
    context: ModuleRunContext = field(default_factory=lambda: ModuleRunContext(module=INDICATOR))


MassIndexReport = VolatilityReport


def normalize_input(request: MassIndexRequest):
    return normalize_volatility_input(request, INPUT_KIND)


def run(request: MassIndexRequest) -> ModuleResult[MassIndexReport]:
    return run_volatility_indicator(INDICATOR, request, input_kind=INPUT_KIND, module_name=INDICATOR)


__all__ = ["MassIndexParams", "MassIndexRequest", "MassIndexReport", "normalize_input", "run"]
